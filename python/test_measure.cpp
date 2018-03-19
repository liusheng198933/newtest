#include <bm/spdlog/spdlog.h>
#include <iostream>
#include <bm/bm_sim/logger.h>
#include <string>

int main()
{
    bm::Logger::get()->debug("haha");
}
