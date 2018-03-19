#!/bin/bash

p4c-bm2-ss --p4v 14 test_router.p4 --p4runtime-file test_router.proto.txt --p4runtime-format text
p4c-bmv2 test_router.p4 --json test_router.json
