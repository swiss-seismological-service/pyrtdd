"""obspy <-> `pyrtdd.hdd.Catalog` conversion.

This module is not imported by `pyrtdd` or `pyrtdd.hdd`, so obspy is only
required if you actually use it (`pip install pyrtdd[obspy]`).

Mirrors scrtdd's own SeisComP<->HDD::Catalog conversion (its
libs/hddsc/utils.cpp, `addToCatalog`/`convertOrigin`), since SeisComP's data
model is QuakeML-based like obspy's -- see that file for the reference this
was built from.
"""

import logging
import math

import obspy
import obspy.core.event
import obspy.geodetics

from pyrtdd.hdd import Catalog
from pyrtdd.obspy.waveform import _to_hdd_time, _to_utcdatetime

_logger = logging.getLogger(__name__)


def _pick_uncertainty(pick):
    errors = pick.time_errors
    if errors is None:
        return float("nan"), float("nan")
    if errors.uncertainty is not None:
        return errors.uncertainty, errors.uncertainty
    if errors.lower_uncertainty is not None and errors.upper_uncertainty is not None:
        return errors.lower_uncertainty, errors.upper_uncertainty
    return float("nan"), float("nan")


def _is_pick_used(pick, arrival):
    if pick.evaluation_mode == "manual":
        return True
    return bool(arrival.time_weight)


def _resolve_station_coordinates(inventory, net, sta, loc, cha, time):
    """Resolve (latitude, longitude, elevation, locationCode, channelCode)
    for a station, tolerating picks whose `waveform_id` doesn't carry a
    location/channel code precise enough for an exact match.

    `locationCode`/`channelCode` in the result are whatever `net.sta.loc.cha`
    was actually matched in the inventory to obtain the coordinates below --
    not necessarily `loc`/`cha` as passed in -- since the caller needs those
    to populate the phase's own `locationCode`/`channelCode` correctly (a
    pick with a missing/wrong location or channel code would otherwise leave
    the resulting catalog referencing a location/channel that doesn't
    actually exist).

    Tries, in order:
    1. `net.sta.loc.cha` exactly as named by the pick. `loc`/`cha` are
       returned unchanged.
    2. If that fails, gather every channel of `net.sta` active at `time`,
       narrowed to `loc` if it's non-empty and to `cha` if it's non-empty
       (an empty `loc`/`cha` is treated as "unspecified", not as a literal
       blank code to filter on). This only resolves if what's left is
       unambiguous:
       - exactly one distinct location code among the candidates -- so if
         `loc` was empty and the station has channels at more than one
         location, resolution fails rather than guessing which one;
       - exactly one distinct band+instrument code (channel code without
         its last, orientation, character) among the candidates -- so
         e.g. co-located "HH?" and "BH?" channels also fail to resolve,
         even though they'd agree on coordinates;
       - and, as a final sanity check, all candidates agree on coordinates
         (channels sharing a location code are normally co-located, but
         this is checked rather than assumed).
       `locationCode` becomes that one location. `channelCode` becomes the
       single candidate's own full code if there's exactly one left (e.g.
       `cha` was given, or only one component exists), otherwise there's
       more than one but they're all components of the same instrument
       (step 2's second bullet), and which specific one the pick actually
       came from can't be determined -- `channelCode` is then just the
       shared band+instrument code (2 characters, no orientation letter).

    Raises the exception from step 1 if the fallback can't resolve either.
    """
    try:
        coords = inventory.get_coordinates(f"{net}.{sta}.{loc}.{cha}", time)
        return {**coords, "locationCode": loc, "channelCode": cha}
    except Exception as exc:
        error = exc

    try:
        selected = inventory.select(network=net, station=sta, time=time)
        channels = [c for n in selected for s in n for c in s]
        if loc:
            channels = [c for c in channels if c.location_code == loc]
        if cha:
            channels = [c for c in channels if c.code == cha]

        locs = {c.location_code for c in channels}
        roots = {c.code[:2] for c in channels}
        coordSet = {(c.latitude, c.longitude, c.elevation) for c in channels}

        if channels and len(locs) == 1 and len(roots) == 1 and len(coordSet) == 1:
            latitude, longitude, elevation = next(iter(coordSet))
            resolvedCha = cha or (
                channels[0].code if len(channels) == 1 else next(iter(roots))
            )
            return {
                "latitude": latitude,
                "longitude": longitude,
                "elevation": elevation,
                "locationCode": next(iter(locs)),
                "channelCode": resolvedCha,
            }
    except Exception:
        pass

    raise error


def catalog_from_obspy(
    obspy_catalog, inventory, discard_unused_automatic_picks=False
):
    """Build a `pyrtdd.hdd.Catalog` from an `obspy.core.event.Catalog` (or
    any iterable of `obspy.core.event.Event`) and an `obspy.Inventory`.

    Each event's preferred origin (falling back to its first origin) becomes
    one HDD event, using the parent event's preferred magnitude (falling
    back to its first, or NaN if there's none at all). Its arrivals become
    HDD phases, with the phase type taken from `Arrival.phase` (falling back
    to the pick's `phase_hint`). Events with no origin, no arrivals, or a
    origin with no depth are skipped, since HDD requires all three.

    Stations are added lazily, one per (network, station, location) actually
    referenced by a used phase, resolved from `inventory` at that phase's
    pick time -- see `_resolve_station_coordinates` for how a pick with a
    missing or non-matching location/channel code still falls back to a
    usable coordinate, but only when the inventory leaves no ambiguity about
    which one. The phase's own `locationCode`/`channelCode` are set from
    whatever `_resolve_station_coordinates` actually matched, not
    necessarily the pick's own (possibly missing or wrong) values -- so e.g.
    a pick with no location code ends up with the real one, not "". If the
    pick's channel code was missing and multiple components of the same
    instrument were viable (e.g. any of "HHZ"/"HHN"/"HHE"), `channelCode`
    ends up as just the shared 2-character band+instrument code ("HH"),
    not a guessed orientation. A phase whose station can't be resolved
    unambiguously even with that fallback is skipped (its event is still
    created, just without that phase). Resolution is cached per distinct
    (network, station, location, channel) as named by the picks themselves,
    so it only hits `inventory` once per distinct combination even across
    many events/phases.

    If `discard_unused_automatic_picks` is True, non-manual picks with a
    zero or missing `Arrival.time_weight` are skipped, matching scrtdd's own
    SeisComP-catalog behavior. This defaults to False here because, unlike
    SeisComP's own database, `time_weight` is often left unset entirely in
    obspy/QuakeML catalogs pulled from other sources (e.g. FDSN event
    services) even for picks that were genuinely used -- enabling this on
    such a catalog can silently discard most or all of it.
    """

    cat = Catalog()
    resolved_cache = {}  # (net, sta, loc, cha) -> resolved coords dict, or None

    for event in obspy_catalog:
        origin = event.preferred_origin()
        if origin is None and event.origins:
            origin = event.origins[0]
        if origin is None or not origin.arrivals:
            _logger.warning(
                "Event %s has no origin or no arrivals, skipping it",
                event.resource_id,
            )
            continue
        if origin.depth is None:
            _logger.warning(
                "Origin %s has no depth, skipping its event", origin.resource_id
            )
            continue

        magnitude = event.preferred_magnitude()
        if magnitude is None and event.magnitudes:
            magnitude = event.magnitudes[0]

        ev = Catalog.Event()
        ev.id = 0  # reassigned by addEvent below
        ev.time = _to_hdd_time(origin.time)
        ev.latitude = origin.latitude
        ev.longitude = origin.longitude
        ev.depth = origin.depth / 1000.0  # obspy: meters, HDD: km
        ev.magnitude = magnitude.mag if magnitude is not None else float("nan")
        newEventId = cat.addEvent(ev, False)

        picks_by_id = {str(p.resource_id): p for p in event.picks}

        for arrival in origin.arrivals:
            pick = picks_by_id.get(str(arrival.pick_id))
            if pick is None:
                _logger.warning(
                    "Cannot find pick %s (origin %s), skipping this phase",
                    arrival.pick_id, origin.resource_id,
                )
                continue

            if discard_unused_automatic_picks and not _is_pick_used(pick, arrival):
                continue

            wid = pick.waveform_id
            net = wid.network_code or ""
            sta = wid.station_code or ""
            rawLoc = wid.location_code or ""
            rawCha = wid.channel_code or ""

            # Resolution (and thus the actual location/channel code) can
            # depend on the pick's own, possibly incomplete, location/channel
            # code -- see `_resolve_station_coordinates` -- so it must happen
            # before `stationId` is computed below, not after.
            cacheKey = (net, sta, rawLoc, rawCha)
            if cacheKey not in resolved_cache:
                try:
                    resolved_cache[cacheKey] = _resolve_station_coordinates(
                        inventory, net, sta, rawLoc, rawCha, pick.time
                    )
                except Exception as e:
                    _logger.warning(
                        "Cannot resolve station %s.%s.%s.%s in the inventory "
                        "(%s), skipping this phase",
                        net, sta, rawLoc, rawCha, e,
                    )
                    resolved_cache[cacheKey] = None
            coords = resolved_cache[cacheKey]
            if coords is None:
                continue

            loc = coords["locationCode"]
            cha = coords["channelCode"]
            stationId = f"{net}.{sta}.{loc}"

            if stationId not in cat.getStations():
                cat.addStation(
                    Catalog.Station(
                        stationId,
                        coords["latitude"],
                        coords["longitude"],
                        coords["elevation"],
                        net,
                        sta,
                        loc,
                    )
                )

            lower, upper = _pick_uncertainty(pick)

            ph = Catalog.Phase()
            ph.eventId = newEventId
            ph.stationId = stationId
            ph.time = _to_hdd_time(pick.time)
            ph.lowerUncertainty = lower
            ph.upperUncertainty = upper
            ph.type = arrival.phase or pick.phase_hint or ""
            ph.networkCode = net
            ph.stationCode = sta
            ph.locationCode = loc
            ph.channelCode = cha
            cat.addPhase(ph)

    return cat


def catalog_to_obspy(hdd_catalog):
    """Build an `obspy.core.event.Catalog` from a `pyrtdd.hdd.Catalog`, e.g.
    the relocated catalog returned by `relocateMultiEvents`, for writing
    results out as QuakeML or plotting with obspy (`cat.plot()`).

    One obspy `Event` (with one `Origin`) is created per HDD event, with
    fresh `Pick`/`Arrival` objects for every associated phase -- these are
    new objects, not whatever originally produced the input catalog -- each
    carrying `relocInfo`'s weight/residual (0 for phases that weren't
    relocated) and, where the phase's station can be found, azimuth and
    distance.
    """

    stations = hdd_catalog.getStations()
    phases_by_event = hdd_catalog.getPhases()

    events = []
    for eventId, event in hdd_catalog.getEvents().items():
        origin = obspy.core.event.Origin(
            time=_to_utcdatetime(event.time),
            latitude=event.latitude,
            longitude=event.longitude,
            depth=event.depth * 1000.0,  # HDD: km, obspy: meters
            evaluation_mode="automatic",
        )

        picks = []
        arrivals = []
        for phase in phases_by_event.get(eventId, []):
            pick = obspy.core.event.Pick(
                time=_to_utcdatetime(phase.time),
                phase_hint=phase.type,
                waveform_id=obspy.core.event.WaveformStreamID(
                    network_code=phase.networkCode,
                    station_code=phase.stationCode,
                    location_code=phase.locationCode,
                    channel_code=phase.channelCode,
                ),
                evaluation_mode="automatic",
            )
            if math.isfinite(phase.lowerUncertainty):
                pick.time_errors.lower_uncertainty = phase.lowerUncertainty
            if math.isfinite(phase.upperUncertainty):
                pick.time_errors.upper_uncertainty = phase.upperUncertainty
            picks.append(pick)

            arrival = obspy.core.event.Arrival(
                pick_id=pick.resource_id,
                phase=phase.type,
                time_weight=(
                    phase.relocInfo.weight if phase.relocInfo.isRelocated else 0.0
                ),
                time_residual=(
                    phase.relocInfo.finalResidual
                    if phase.relocInfo.isRelocated
                    else 0.0
                ),
            )
            station = stations.get(phase.stationId)
            if station is not None:
                try:
                    _, azimuth, _ = obspy.geodetics.gps2dist_azimuth(
                        event.latitude, event.longitude,
                        station.latitude, station.longitude,
                    )
                    arrival.azimuth = azimuth % 360.0
                    arrival.distance = obspy.geodetics.locations2degrees(
                        event.latitude, event.longitude,
                        station.latitude, station.longitude,
                    )
                except Exception as e:
                    _logger.warning(
                        "Cannot compute azimuth/distance for phase %s: %s",
                        phase, e,
                    )
            arrivals.append(arrival)

        origin.arrivals = arrivals

        ev = obspy.core.event.Event(
            picks=picks,
            origins=[origin],
            preferred_origin_id=origin.resource_id,
        )
        if not math.isnan(event.magnitude):
            magnitude = obspy.core.event.Magnitude(
                mag=event.magnitude, origin_id=origin.resource_id
            )
            ev.magnitudes = [magnitude]
            ev.preferred_magnitude_id = magnitude.resource_id

        events.append(ev)

    return obspy.core.event.Catalog(events=events)
