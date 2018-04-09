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

header_type intrinsic_metadata_t {
    fields {
        mcast_grp : 4;
        egress_rid : 4;
        mcast_hash : 16;
        lf_field_list : 32;
        resubmit_flag : 16;
    }
}

header_type circle_ct {
    fields {
        ct : 8;
    }
}

header_type rtmp_ttmp {
    fields {
        rtmp : 32;
        ttmp: 32;
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
metadata intrinsic_metadata_t intrinsic_metadata;
metadata circle_ct circt;
metadata rtmp_ttmp rttmp;

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


parser parse_ipv4 {
    extract(ipv4);
    return ingress;
}


action _drop() {
    drop();
}


action set_nhop(rtmp, ttmp, port) {
    modify_field(standard_metadata.egress_spec, port);
    modify_field(rttmp.rtmp, rtmp);
    modify_field(rttmp.ttmp, ttmp);
}

action _set_tmp() {
    modify_field(pktTMP.tmp, rttmp.ttmp);
    modify_field(ipv4.ttl, ipv4.ttl - 1);
}

field_list resubmit_FL {
    circt;
}

action _resubmit() {
    modify_field(circt.ct, 1); //Metadata instances are initialized to 0 by default
    resubmit(resubmit_FL);
}

table ipv4_lpm {
    reads {
        ipv4.srcAddr : ternary;
        ipv4.dstAddr : ternary;
        //pktTMP.tmp : range; // a..b
    }
    actions {
        set_nhop;
        _drop;
    }
    size: 1024;
}

table resubmit_table {
    actions {
        _resubmit;
    }
    size: 1024;
}

table action_table {
    actions {
        _set_tmp;
    }
    size: 1024;
}


control ingress {
    if(valid(pktTMP) and valid(ipv4) and ipv4.ttl > 0) {
        apply(ipv4_lpm);
    }
    if (valid(pktTMP) and rttmp.rtmp < pktTMP.tmp){
        apply(resubmit_table);
    }
    if (valid(pktTMP) and rttmp.rtmp >= pktTMP.tmp){
        apply(action_table);
    }
}

control egress {
    //apply(send_frame);
}
