/* Copyright 2013-present Barefoot Networks, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

header_type ethernet_t {
    fields {
        dstAddr : 48;
        srcAddr : 48;
        etherType : 16;
    }
}

header_type timestamp_t {
    fields {
        preamble : 64;
        tmp : 32;
    }
}

header_type circle_ct {
    fields {
        ct : 8;
    }
}

header_type ipv4_t {
    fields {
        version : 4;
        ihl : 4;
        diffserv : 8;
        totalLen : 16;
        identification : 16;
        flags : 3;
        fragOffset : 13;
        ttl : 8;
        protocol : 8;
        hdrChecksum : 16;
        srcAddr : 32;
        dstAddr: 32;
    }
}

header timestamp_t pktTMP;
metadata circle_ct circt;

parser start {
    return select(current(0, 64)) {
        0 : parse_timestamp;
        default: parse_ethernet;
    }
}

#define ETHERTYPE_IPV4 0x0800

header ethernet_t ethernet;

parser parse_timestamp {
    extract(pktTMP);
    return parse_ethernet;
}

parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
        ETHERTYPE_IPV4 : parse_ipv4;
        default: ingress;
    }
}

header ipv4_t ipv4;

field_list ipv4_checksum_list {
        ipv4.version;
        ipv4.ihl;
        ipv4.diffserv;
        ipv4.totalLen;
        ipv4.identification;
        ipv4.flags;
        ipv4.fragOffset;
        ipv4.ttl;
        ipv4.protocol;
        ipv4.srcAddr;
        ipv4.dstAddr;
}

field_list_calculation ipv4_checksum {
    input {
        ipv4_checksum_list;
    }
    algorithm : csum16;
    output_width : 16;
}

calculated_field ipv4.hdrChecksum  {
    verify ipv4_checksum;
    update ipv4_checksum;
}

parser parse_ipv4 {
    extract(ipv4);
    return ingress;
}


action _drop() {
    drop();
}


action set_nhop(ttmp, port) {
    modify_field(standard_metadata.egress_spec, port);
    modify_field(ipv4.ttl, ipv4.ttl - 1);
    modify_field(pktTMP.tmp, ttmp);
}

field_list resubmit_FL {
    circt;
}

action _resubmit() {
    modify_field(circt.ct, circt.ct); //Metadata instances are initialized to 0 by default
    resubmit(resubmit_FL);
}

table ipv4_lpm {
    reads {
        ipv4.dstAddr : lpm;
        pktTMP.tmp : range; // a..b
    }
    actions {
        set_nhop;
        _resubmit;
        _drop;
    }
    size: 1024;
}


control ingress {
    if(valid(pktTMP) and valid(ipv4) and ipv4.ttl > 0) {
        apply(ipv4_lpm);
    }
}

control egress {
    //apply(send_frame);
}