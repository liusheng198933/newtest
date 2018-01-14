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

/*
 * Antonin Bas (antonin@barefootnetworks.com)
 *
 */

#include <grpc++/grpc++.h>

#include <google/rpc/code.pb.h>
#include <p4/p4runtime.grpc.pb.h>
#include <p4/tmp/p4config.grpc.pb.h>

#include <google/protobuf/util/message_differencer.h>

#include <fstream>
#include <memory>
#include <streambuf>
#include <string>
#include <thread>
#include <chrono>

#include "utils.h"

namespace sswitch_grpc {

namespace testing {

namespace {

using grpc::ClientContext;
using grpc::Status;

using google::protobuf::util::MessageDifferencer;

constexpr char test_json[] = "/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.json";
constexpr char test_proto_txt[] = "/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.proto.txt";

int
switch_init(int dev_id, std::string channel_port) {
  //int dev_id = 0;

  auto channel = grpc::CreateChannel(
      channel_port, grpc::InsecureChannelCredentials());
  std::unique_ptr<p4::P4Runtime::Stub> pi_stub_(
      p4::P4Runtime::NewStub(channel));

  auto p4info = parse_p4info(test_proto_txt);

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

  {
    p4::SetForwardingPipelineConfigRequest request;
    request.set_device_id(dev_id);
    request.set_action(
        p4::SetForwardingPipelineConfigRequest_Action_VERIFY_AND_COMMIT);
    set_election_id(request.mutable_election_id());
    auto config = request.mutable_config();
    config->set_allocated_p4info(&p4info);
    p4::tmp::P4DeviceConfig device_config;
    std::ifstream istream(test_json);
    device_config.mutable_device_data()->assign(
        (std::istreambuf_iterator<char>(istream)),
         std::istreambuf_iterator<char>());
    device_config.SerializeToString(config->mutable_p4_device_config());

    p4::SetForwardingPipelineConfigResponse rep;
    ClientContext context;
    auto status = pi_stub_->SetForwardingPipelineConfig(
        &context, request, &rep);
    assert(status.ok());
    config->release_p4info();
  }

  {
    stream->WritesDone();
    p4::StreamMessageResponse response;
    while (stream->Read(&response)) { }
    auto status = stream->Finish();
    assert(status.ok());
  }

  return 0;
}


int
rule_mod(int dev_id, std::string channel_port, int mod_flag, std::string ip_addr, std::string rtmp_low, std::string rtmp_high, int action_flag, std::string ttmp, std::string out_port) {
  //int dev_id = 0;

  auto channel = grpc::CreateChannel(
      channel_port, grpc::InsecureChannelCredentials());
  std::unique_ptr<p4::P4Runtime::Stub> pi_stub_(
      p4::P4Runtime::NewStub(channel));

  auto p4info = parse_p4info(test_proto_txt);

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

  auto t_id = get_table_id(p4info, "ipv4_lpm");
  auto mf0_id = get_mf_id(p4info, "ipv4_lpm", "ipv4.dstAddr");
  auto mf1_id = get_mf_id(p4info, "ipv4_lpm", "pktTMP.tmp");
  auto a0_id = get_action_id(p4info, "set_nhop");
  auto p0_id = get_param_id(p4info, "set_nhop", "ttmp");
  auto p1_id = get_param_id(p4info, "set_nhop", "port");
  auto a1_id = get_action_id(p4info, "_resubmit");
  auto a2_id = get_action_id(p4info, "_drop");

{
  p4::Entity entity;
  auto table_entry = entity.mutable_table_entry();
  table_entry->set_table_id(t_id);
  {
    auto match = table_entry->add_match();
    match->set_field_id(mf0_id);
    auto lpm = match->mutable_lpm();
    lpm->set_value(ip_addr);  // 10.0.0.10
    lpm->set_prefix_len(24);
  }
  {
    auto match = table_entry->add_match();
    match->set_field_id(mf1_id);
    //auto rng = match->mutable_exact(); // exact
    //rng->set_value(rtmp_high);
    auto rng = match->mutable_range();
    rng->set_low(rtmp_low);  // range
    rng->set_high(rtmp_high);
  }

  auto table_action = table_entry->mutable_action();
  auto action = table_action->mutable_action();
  if (action_flag == 0){
    action->set_action_id(a0_id);
    {
      auto param = action->add_params();
      param->set_param_id(p0_id);
      param->set_value(ttmp);  // ttmp
    }
    {
      auto param = action->add_params();
      param->set_param_id(p1_id);
      param->set_value(out_port);  // port 1
    }
  }

  if (action_flag == 1){
    action->set_action_id(a1_id);
  }

  if (action_flag == 2){
    action->set_action_id(a2_id);
  }


  // add entry
  {
    p4::WriteRequest request;
    set_election_id(request.mutable_election_id());
    request.set_device_id(dev_id);
    auto update = request.add_updates();
    if (mod_flag == 0){
      update->set_type(p4::Update_Type_INSERT);
    }
    if (mod_flag == 1){
      update->set_type(p4::Update_Type_DELETE);
    }
    update->set_allocated_entity(&entity);
    ClientContext context;
    p4::WriteResponse rep;
    auto status = pi_stub_->Write(&context, request, &rep);
    if (!status.ok()) {
      std::cout << status.error_code() << ": " << status.error_message()
                << std::endl;
    }
    assert(status.ok());
    update->release_entity();
  }
}

  {
    stream->WritesDone();
    p4::StreamMessageResponse response;
    while (stream->Read(&response)) { }
    auto status = stream->Finish();
    assert(status.ok());
  }

  return 0;
}


int
rule_read(int dev_id, std::string channel_port) {
  //int dev_id = 0;

  auto channel = grpc::CreateChannel(
      channel_port, grpc::InsecureChannelCredentials());
  std::unique_ptr<p4::P4Runtime::Stub> pi_stub_(
      p4::P4Runtime::NewStub(channel));

  auto p4info = parse_p4info(test_proto_txt);

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

  auto t_id = get_table_id(p4info, "ipv4_lpm");
  auto mf0_id = get_mf_id(p4info, "ipv4_lpm", "ipv4.dstAddr");
  auto mf1_id = get_mf_id(p4info, "ipv4_lpm", "pktTMP.tmp");
  auto a0_id = get_action_id(p4info, "set_nhop");
  auto p0_id = get_param_id(p4info, "set_nhop", "ttmp");
  auto p1_id = get_param_id(p4info, "set_nhop", "port");
  auto a1_id = get_action_id(p4info, "_resubmit");
  auto a2_id = get_action_id(p4info, "_drop");

  {
    p4::Entity entity;
    auto table_entry = entity.mutable_table_entry();
    table_entry->set_table_id(t_id);
    auto read_one = [&dev_id, &pi_stub_, &table_entry] () {
    p4::ReadRequest request;
    request.set_device_id(dev_id);
    auto entity = request.add_entities();
    entity->set_allocated_table_entry(table_entry);
    ClientContext context;
    std::unique_ptr<grpc::ClientReader<p4::ReadResponse> > reader(
        pi_stub_->Read(&context, request));
    p4::ReadResponse rep;
    reader->Read(&rep);
    auto status = reader->Finish();
    if (!status.ok()) {
      std::cout << status.error_code() << ": " << status.error_message()
                << std::endl;
    }
    //assert(status.ok());
    entity->release_table_entry();
    return rep;
  };

  // get entry, check it is the one we added
  {
    auto rep = read_one();
    std::cout << rep.entities().size() << std::endl;
    //assert(rep.entities().size() == 1);
    //assert(MessageDifferencer::Equals(entity, rep.entities().Get(0)));
  }
}


  {
    stream->WritesDone();
    p4::StreamMessageResponse response;
    while (stream->Read(&response)) { }
    auto status = stream->Finish();
    assert(status.ok());
  }

  return 0;
}


int
rule_mod_base(std::unique_ptr<p4::P4Runtime::Stub> & pi_stub_, int dev_id, std::string channel_port, int mod_flag, std::string ip_addr, std::string rtmp_low, std::string rtmp_high, int action_flag, std::string ttmp, std::string out_port) {
  //int dev_id = 0;

  auto set_election_id = [](p4::Uint128 *election_id) {
    election_id->set_high(0);
    election_id->set_low(1);
  };

  auto p4info = parse_p4info(test_proto_txt);

  auto t_id = get_table_id(p4info, "ipv4_lpm");
  auto mf0_id = get_mf_id(p4info, "ipv4_lpm", "ipv4.dstAddr");
  auto mf1_id = get_mf_id(p4info, "ipv4_lpm", "pktTMP.tmp");
  auto a0_id = get_action_id(p4info, "set_nhop");
  auto p0_id = get_param_id(p4info, "set_nhop", "ttmp");
  auto p1_id = get_param_id(p4info, "set_nhop", "port");
  auto a1_id = get_action_id(p4info, "_resubmit");
  auto a2_id = get_action_id(p4info, "_drop");

{
  p4::Entity entity;
  auto table_entry = entity.mutable_table_entry();
  table_entry->set_table_id(t_id);
  {
    auto match = table_entry->add_match();
    match->set_field_id(mf0_id);
    auto lpm = match->mutable_lpm();
    lpm->set_value(ip_addr);  // 10.0.0.10
    lpm->set_prefix_len(24);
  }
  {
    auto match = table_entry->add_match();
    match->set_field_id(mf1_id);
    //auto rng = match->mutable_exact(); // exact
    //rng->set_value(rtmp_high);
    auto rng = match->mutable_range();
    rng->set_low(rtmp_low);  // range
    rng->set_high(rtmp_high);
  }

  auto table_action = table_entry->mutable_action();
  auto action = table_action->mutable_action();
  if (action_flag == 0){
    action->set_action_id(a0_id);
    {
      auto param = action->add_params();
      param->set_param_id(p0_id);
      param->set_value(ttmp);  // ttmp
    }
    {
      auto param = action->add_params();
      param->set_param_id(p1_id);
      param->set_value(out_port);  // port 1
    }
  }

  if (action_flag == 1){
    action->set_action_id(a1_id);
  }

  if (action_flag == 2){
    action->set_action_id(a2_id);
  }


  // add entry
  {
    p4::WriteRequest request;
    set_election_id(request.mutable_election_id());
    request.set_device_id(dev_id);
    auto update = request.add_updates();
    if (mod_flag == 0){
      update->set_type(p4::Update_Type_INSERT);
    }
    if (mod_flag == 1){
      update->set_type(p4::Update_Type_DELETE);
    }
    update->set_allocated_entity(&entity);
    ClientContext context;
    p4::WriteResponse rep;
    auto status = pi_stub_->Write(&context, request, &rep);
    if (!status.ok()) {
      std::cout << status.error_code() << ": " << status.error_message()
                << std::endl;
    }
    assert(status.ok());
    update->release_entity();
  }
}


  return 0;
}

int
rule_mod_test(int dev_id, std::string channel_port) {
  //int dev_id = 0;

  auto channel = grpc::CreateChannel(
      channel_port, grpc::InsecureChannelCredentials());
  std::unique_ptr<p4::P4Runtime::Stub> pi_stub_(
      p4::P4Runtime::NewStub(channel));

  auto p4info = parse_p4info(test_proto_txt);

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

  rule_mod_base(pi_stub_, dev_id, channel_port, 0, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x00\x00\x01", 4), std::string("\x00\x00\x00\x02", 4), 0, std::string("\x00\x00\x00\x02", 4), std::string("\x00\x01", 2));
  rule_mod_base(pi_stub_, dev_id, channel_port, 0, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x00\x00\x01", 4), std::string("\x00\x00\x00\x02", 4), 0, std::string("\x00\x00\x00\x02", 4), std::string("\x00\x01", 2));


  {
    stream->WritesDone();
    p4::StreamMessageResponse response;
    while (stream->Read(&response)) { }
    auto status = stream->Finish();
    assert(status.ok());
  }

  return 0;
}


int
rule_mod_test1(int dev_id, std::string channel_port) {
  //int dev_id = 0;

  auto channel = grpc::CreateChannel(
      channel_port, grpc::InsecureChannelCredentials());
  std::unique_ptr<p4::P4Runtime::Stub> pi_stub_(
      p4::P4Runtime::NewStub(channel));

  auto p4info = parse_p4info(test_proto_txt);

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

  rule_mod_base(pi_stub_, dev_id, channel_port, 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x00\x00\x03", 4), std::string("\x00\x00\x00\x04", 4), 0, std::string("\x00\x00\x00\x04", 4), std::string("\x00\x02", 2));
  rule_mod_base(pi_stub_, dev_id, channel_port, 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x00\x00\x01", 4), std::string("\x00\x00\x00\x02", 4), 1, std::string("\x00\x00\x00\x02", 4), std::string("\x00\x02", 2));

  {
    stream->WritesDone();
    p4::StreamMessageResponse response;
    while (stream->Read(&response)) { }
    auto status = stream->Finish();
    assert(status.ok());
  }

  return 0;
}

int
rule_mod_test2(int dev_id, std::string channel_port) {
  //int dev_id = 0;

  auto channel = grpc::CreateChannel(
      channel_port, grpc::InsecureChannelCredentials());
  std::unique_ptr<p4::P4Runtime::Stub> pi_stub_(
      p4::P4Runtime::NewStub(channel));

  auto p4info = parse_p4info(test_proto_txt);

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

  rule_mod_base(pi_stub_, dev_id, channel_port, 1, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x00\x00\x03", 4), std::string("\x00\x00\x00\x04", 4), 0, std::string("\x00\x00\x00\x04", 4), std::string("\x00\x02", 2));
  rule_mod_base(pi_stub_, dev_id, channel_port, 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x00\x00\x03", 4), std::string("\x00\x00\x00\x04", 4), 0, std::string("\x00\x00\x00\x04", 4), std::string("\x00\x02", 2));


  {
    stream->WritesDone();
    p4::StreamMessageResponse response;
    while (stream->Read(&response)) { }
    auto status = stream->Finish();
    assert(status.ok());
  }

  return 0;
}

}  // namespace

}  // namespace testing

}  // namespace sswitch_grpc

int network_init(){
  std::string channel_port[4] = {"localhost:50051", "localhost:50052", "localhost:50053", "localhost:50054"};
  for (int dev_id=0; dev_id<4; dev_id++){
    sswitch_grpc::testing::switch_init(dev_id, channel_port[dev_id]);
  }

  //sswitch_grpc::testing::rule_mod(0, channel_port[0], 0, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x01", 2));
  //sswitch_grpc::testing::rule_mod(0, channel_port[0], 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x02", 2));
  //sswitch_grpc::testing::rule_mod(1, channel_port[1], 0, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x01", 2));
  //sswitch_grpc::testing::rule_mod(1, channel_port[1], 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x02", 2));
  //sswitch_grpc::testing::rule_mod(3, channel_port[3], 0, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x01", 2));
  //sswitch_grpc::testing::rule_mod(3, channel_port[3], 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x03", 2));

  for (int dev_id=0; dev_id<4; dev_id++){
    sswitch_grpc::testing::rule_read(dev_id, channel_port[dev_id]);
  }
  return 0;
}

int network_change1(){
  std::string channel_port[4] = {"localhost:50051", "localhost:50052", "localhost:50053", "localhost:50054"};

  //sswitch_grpc::testing::rule_mod(0, channel_port[0], 1, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x02", 2));
  //sswitch_grpc::testing::rule_mod(0, channel_port[0], 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x03", 2));
  //sswitch_grpc::testing::rule_mod(1, channel_port[1], 1, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x01", 2));
  //sswitch_grpc::testing::rule_mod(1, channel_port[1], 1, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x02", 2));
  //sswitch_grpc::testing::rule_mod(2, channel_port[2], 0, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x01", 2));
  //sswitch_grpc::testing::rule_mod(2, channel_port[2], 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x02", 2));
  //sswitch_grpc::testing::rule_mod(3, channel_port[3], 1, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x01", 2));
  //sswitch_grpc::testing::rule_mod(3, channel_port[3], 0, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x03", 2));

  for (int dev_id=0; dev_id<4; dev_id++){
    sswitch_grpc::testing::rule_read(dev_id, channel_port[dev_id]);
  }
  return 0;
}

int network_change2(){
  std::string channel_port[4] = {"localhost:50051", "localhost:50052", "localhost:50053", "localhost:50054"};

  //sswitch_grpc::testing::rule_mod(0, channel_port[0], 0, std::string("\x0a\x00\x02\x0a", 4), std::string("\x00\x01", 2));

  for (int dev_id=0; dev_id<4; dev_id++){
    sswitch_grpc::testing::rule_read(dev_id, channel_port[dev_id]);
  }
  return 0;
}





int
main(int argc, char *argv[]) {
  //int dev_id = 1;
  std::string channel_port[4] = {"localhost:50051", "localhost:50052", "localhost:50053", "localhost:50054"};

  int dev_id = 0;

  sswitch_grpc::testing::switch_init(dev_id, channel_port[dev_id]);
  sswitch_grpc::testing::rule_mod_test1(dev_id, channel_port[0]);
  //std::this_thread::sleep_for (std::chrono::seconds(5));
  //sswitch_grpc::testing::rule_mod_test2(dev_id, channel_port[0]);

  //sswitch_grpc::testing::rule_mod(dev_id, channel_port[0], 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x00\x00\x01", 4), std::string("\x00\x00\x00\x02", 4), 0, std::string("\x00\x00\x00\x02", 4), std::string("\x00\x02", 2));
  //sswitch_grpc::testing::rule_mod(dev_id, channel_port[0], 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x00\x00\x01", 4), std::string("\x00\x00\x00\x02", 4), 1, std::string("\x00\x00\x00\x02", 4), std::string("\x00\x02", 2));
  //sswitch_grpc::testing::rule_read(dev_id, channel_port[dev_id]);
  //std::this_thread::sleep_for (std::chrono::seconds(1));
  //sswitch_grpc::testing::rule_mod(dev_id, channel_port[0], 1, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x00\x00\x01", 4), std::string("\x00\x00\x00\x02", 4), 0, std::string("\x00\x00\x00\x02", 4), std::string("\x00\x02", 2));
  //sswitch_grpc::testing::rule_mod(dev_id, channel_port[0], 0, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x00\x00\x01", 4), std::string("\x00\x00\x00\x02", 4), 0, std::string("\x00\x00\x00\x02", 4), std::string("\x00\x02", 2));

  //sswitch_grpc::testing::rule_mod(3, channel_port[3], 1, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x01", 2));
  //sswitch_grpc::testing::rule_mod(3, channel_port[3], 0, std::string("\x0a\x00\x00\x0a", 4), std::string("\x00\x02", 2));
  //for (int dev_id=0; dev_id<4; dev_id++){
  //  sswitch_grpc::testing::rule_read(dev_id, channel_port[dev_id]);
  //}
  //sswitch_grpc::testing::switch_del(dev_id, var1);

  //sswitch_grpc::testing::test_delete();
  //std::this_thread::sleep_for (std::chrono::seconds(10));
  //sswitch_grpc::testing::test_add();
  //sswitch_grpc::testing::test_read();

  //network_init();
  //std::this_thread::sleep_for (std::chrono::seconds(5));
  //network_change1();
  //std::this_thread::sleep_for (std::chrono::seconds(5));
  //network_change2();

  //sswitch_grpc::testing::rule_mod(0, channel_port[0], 1, std::string("\x0a\x00\x01\x0a", 4), std::string("\x00\x02", 2));
  //sswitch_grpc::testing::rule_read(dev_id, channel_port[dev_id]);

  return 0;
}
