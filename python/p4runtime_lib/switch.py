# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from abc import abstractmethod

import sys
sys.path.insert(0, "/home/shengliu/Workspace/PI/proto/py_out/p4")

import p4runtime_pb2
import p4runtime_pb2_grpc

import grpc
import Queue
import threading

from tmp import p4config_pb2

class SwitchConnection(object):
    def __init__(self, name, address='localhost:50051', device_id=0):
        self.name = name
        self.address = address
        self.device_id = device_id
        self.p4info = None
        self.channel = grpc.insecure_channel(self.address)
        self.client_stub = p4runtime_pb2.P4RuntimeStub(self.channel)
        self.strean = None

    @abstractmethod
    def buildDeviceConfig(self, **kwargs):
        return p4config_pb2.P4DeviceConfig()

    def SetForwardingPipelineConfig(self, p4info, dry_run=False, **kwargs):
        device_config = self.buildDeviceConfig(**kwargs)
        request = p4runtime_pb2.SetForwardingPipelineConfigRequest()
        config = request.configs.add()
        config.device_id = self.device_id
        config.p4info.CopyFrom(p4info)
        config.p4_device_config = device_config.SerializeToString()
        request.action = p4runtime_pb2.SetForwardingPipelineConfigRequest.VERIFY_AND_COMMIT
        if dry_run:
            print "P4 Runtime SetForwardingPipelineConfig:", request
        else:
            self.client_stub.SetForwardingPipelineConfig(request)


    def WriteTableEntry(self, table_entry, dry_run=False, update_flag=0):
        request = p4runtime_pb2.WriteRequest()
        request.device_id = self.device_id
        #print request
        #print request.device_id
        update = request.updates.add()
        if update_flag == 0:
            update.type = p4runtime_pb2.Update.INSERT
        if update_flag == 1:
            update.type = p4runtime_pb2.Update.DELETE
        if update_flag == 2:
            update.type = p4runtime_pb2.Update.MODIFY
        update.entity.table_entry.CopyFrom(table_entry)
        if dry_run:
            print "P4 Runtime Write:", request
        else:
            self.client_stub.Write(request)

    def ReadTableEntries(self, table_id=None, dry_run=False):
        request = p4runtime_pb2.ReadRequest()
        request.device_id = self.device_id
        entity = request.entities.add()
        table_entry = entity.table_entry
        if table_id is not None:
            table_entry.table_id = table_id
        else:
            table_entry.table_id = 0
        if dry_run:
            print "P4 Runtime Read:", request
        else:
            for response in self.client_stub.Read(request):
                yield response

    def ReadCounters(self, counter_id=None, index=None, dry_run=False):
        request = p4runtime_pb2.ReadRequest()
        request.device_id = self.device_id
        entity = request.entities.add()
        counter_entry = entity.counter_entry
        if counter_id is not None:
            counter_entry.counter_id = counter_id
        else:
            counter_entry.counter_id = 0
        if index is not None:
            counter_entry.index = index
        if dry_run:
            print "P4 Runtime Read:", request
        else:
            for response in self.client_stub.Read(request):
                yield response

    def gen(self):
        request = p4runtime_pb2.StreamMessageRequest()
        request.arbitration.device_id = self.device_id
        request.arbitration.election_id.high = 0
        request.arbitration.election_id.low = 1
        for msg in [request]:
            yield msg

    def BuildConnection(self):
        response = self.client_stub.StreamChannel(self.gen())
        request = p4runtime_pb2.StreamMessageRequest()
        request.arbitration.device_id = self.device_id
        request.arbitration.election_id.high = 0
        request.arbitration.election_id.low = 1

    def set_up_stream(self):
        self.stream_out_q = Queue.Queue()
        self.stream_in_q = Queue.Queue()
        def stream_req_iterator():
            while True:
                p = self.stream_out_q.get()
                if p is None:
                    break
                yield p

        def stream_recv(stream):
            for p in stream:
                self.stream_in_q.put(p)

        self.stream = self.client_stub.StreamChannel(stream_req_iterator())
        #self.stream_recv_thread = threading.Thread(
        #    target=stream_recv, args=(self.stream,))
        #self.stream_recv_thread.start()

        self.handshake()

    def handshake(self):
        req = p4runtime_pb2.StreamMessageRequest()
        arbitration = req.arbitration
        arbitration.device_id = self.device_id
        # TODO(antonin): we currently allow 0 as the election id in P4Runtime;
        # if this changes we will need to use an election id > 0 and update the
        # Write message to include the election id
        #election_id = arbitration.election_id
        #election_id.high = 0
        #election_id.low = 1
        self.stream_out_q.put(req)

        #rep = self.get_stream_packet("arbitration", timeout=2)
        #if rep is None:
        #    self.fail("Failed to establish handshake")


        #print response[0].arbitration.status.code
