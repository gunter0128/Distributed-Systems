#ifndef RPCS_H
#define RPCS_H

#include "chord.h"
#include "rpc/client.h"
#include <iostream>
#include <vector>
#include <exception>
#include <unistd.h>
#include <math.h>

// 定義 Chord 的參數
#define finger_table_size 4 // Finger Table 的大小
#define successor_list_size 3 // Successor List 的大小

// 節點相關變數
Node self, successor, predecessor;
std::vector<Node> finger_table(finger_table_size, self);
std::vector<Node> successor_list(successor_list_size, self);
int finger_idx = -1;
int next_idx = -1;

// 節點輔助函式
bool between(uint64_t id, uint64_t start, uint64_t end);
bool in_range(uint64_t x, uint64_t start, uint64_t end);


Node closest_preceding_node(uint64_t id); // 找到最接近的前序節點
Node find_successor(uint64_t id); // 找到最接近的後繼節點

Node get_info() { return self; }

Node get_successor() { return successor; }

Node get_predecessor() { return predecessor; }

// 節點行為函式
void create(); // 初始化 Chord 環
void join(Node n); // 加入現有的 Chord 環
void notify(Node n); // 更新前驅節點
void stabilize(); // 穩定 Chord 環
void fix_finger(); // 修復 Finger Table
void fix_successor(); // 修復 Successor List
void check_predecessor(); // 驗證前驅節點是否存活

// 註冊函式
void register_rpcs(); // 註冊 RPC 方法
void register_periodics(); // 註冊定期執行的任務

//
// 節點輔助函式定義
//

bool between(uint64_t id, uint64_t start, uint64_t end) {
  if (start == end) return true;
  return (start < end) ? (id > start && id <= end) : (id > start || id <= end);
}

bool in_range(uint64_t x, uint64_t start, uint64_t end) {
  if (start == end) return false;
  return (start < end) ? (x > start && x < end) : (x > start || x < end);
}

void create() {
  predecessor.ip = "";
  successor = self;
}


Node closest_preceding_node(uint64_t id) {
  for (int i = finger_table_size - 1; i >= 0; i--) {
    if (!finger_table[i].ip.empty() && between(finger_table[i].id, self.id, id)) {
      return finger_table[i];
    }
  }
  return self;
}

Node find_successor(uint64_t id) {
  if (id == successor.id || between(id, self.id, successor.id)) {
    return successor;
  }
  Node n = closest_preceding_node(id);
  if (n.id == self.id) {
    return successor;
  }
  rpc::client client(n.ip, n.port);
  return client.call("find_successor", id).as<Node>();
}

void notify(Node n) {
  if (predecessor.ip.empty() || between(n.id, predecessor.id, self.id)) {
    predecessor = n;
  }
}

void stabilize() {
  if (!successor.ip.empty()) {
    try {
      rpc::client client(successor.ip, successor.port);
      Node x = client.call("get_predecessor").as<Node>();
      if (!x.ip.empty() && between(x.id, self.id, successor.id)) {
        successor = x;
      }
      client.call("notify", self);
    } catch (std::exception &e) {
      for (auto &node : successor_list) {
        if (!node.ip.empty()) {
          successor = node;
          break;
        }
      }
    }
  }
}

void fix_finger(){
  if(successor.ip != "" && predecessor.ip != ""){
    finger_idx = finger_idx + 1;
    if (finger_idx >= finger_table_size){
      finger_idx = 0;
    }

    uint64_t start = (self.id + (uint64_t)pow(2, 24 + finger_idx)) % (uint64_t)pow(2, 32);
    finger_table[finger_idx] = find_successor(start);
  }
}

void join(Node n) {
  predecessor.ip = "";
  rpc::client client(n.ip, n.port);
  successor = client.call("find_successor", self.id).as<Node>();
}

void fix_successor(){

  if (successor.ip != ""){
    Node next_node;
    try{
      next_idx = next_idx + 1;
      if (next_idx >= successor_list_size){
        next_idx = 0;
      }

      if (next_idx == 0){
        successor_list[next_idx] = successor;
      }
      else{
        next_node = successor_list[next_idx - 1];
        try
        {
          rpc::client client3(next_node.ip, next_node.port);
          if (next_node.id == self.id)
          {
            successor_list[next_idx] = successor;
            return;
          }
  
          successor_list[next_idx] = client3.call("get_successor").as<Node>();
          next_node = successor_list[next_idx];
        }
        catch (std::exception &e)
        {
          for (int k = 0; k < successor_list_size - next_idx; k++){
            successor_list[next_idx - 1 + k] = successor_list[next_idx + k];
          }
          next_idx = - 1;
        }
      }
    }
    catch(std::exception &e){
    }
  }
}

void check_predecessor() {
  try {
    rpc::client client(predecessor.ip, predecessor.port);
    client.call("get_info").as<Node>();
  } catch (std::exception &e) {
    predecessor.ip = ""; // 無法連接時，將前驅設為空
  }
}


//
// 註冊函式定義
//

void register_rpcs() {
  add_rpc("get_info", &get_info);
  add_rpc("get_successor", &get_successor);
  add_rpc("get_predecessor", &get_predecessor);
  add_rpc("find_successor", &find_successor);
  add_rpc("between", &between);
  add_rpc("notify", &notify);
  add_rpc("stabilize", &stabilize);
  add_rpc("create", &create);
  add_rpc("join", &join);
}

void register_periodics() {
  add_periodic(check_predecessor);
  add_periodic(stabilize);
  add_periodic(fix_finger);
  add_periodic(fix_successor);
}

#endif /* RPCS_H */
