import sys
sys.path.insert(0, "/home/shengliu/Workspace/PI/proto/py_out/p4")

import grpc

import p4runtime_pb2
import p4runtime_pb2_grpc
from p4.tmp import p4config_pb2
from helper import *

test_json = "/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.json"
test_proto_txt = "/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.proto.txt"

def switch_init():
  channel = grpc.insecure_channel('localhost:50051')
  stub = p4runtime_pb2_grpc.P4RuntimeStub(channel)

  p4info_helper = P4InfoHelper(test_proto_txt)

  response = stub.SayHello(helloworld_pb2.HelloRequest(name='you'))
  print("p4runtime client received: " + response.message)


if __name__ == '__main__':
  switch_init()


auto set_election_id = [](p4::Uint128 *election_id) {
election_id->set_high(0);
election_id->set_low(1);
};

// initial handshake: open bidirectional stream and advertise election
// id. This stream needs to stay open for the lifetime of the controller.
ClientContext stream_context;
auto stream = pi_stub_->StreamChannel(&stream_context);
{
p4::StreamMessageRequest request;
auto arbitration = request.mutable_arbitration();
arbitration->set_device_id(dev_id);
set_election_id(arbitration->mutable_election_id());
stream->Write(request);
p4::StreamMessageResponse response;
stream->Read(&response);
assert(response.update_case() == p4::StreamMessageResponse::kArbitration);
assert(response.arbitration().status().code() == ::google::rpc::Code::OK);
}
