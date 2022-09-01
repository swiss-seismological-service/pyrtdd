#include "catch2/catch_session.hpp"

auto main(int argc, char *argv[]) -> int {
  return Catch::Session().run(argc, argv);
}