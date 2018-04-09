#include <deque>
#include <mutex>
#include <condition_variable>
#include <iostream>
#include <chrono>
#include <thread>
#include <cstdio>
#include <ctime>


template <class T>
class Queue {
 public:
  //! Implementation behavior when an item is pushed to a full queue
  enum WriteBehavior {
    //! block and wait until a slot is available
    WriteBlock,
    //! return immediately
    WriteReturn
  };
  //! Implementation behavior when an element is popped from an empty queue
  enum ReadBehavior {
    //! block and wait until the queue becomes non-empty
    ReadBlock,
    //! not implemented yet
    ReadReturn
  };

 public:
  Queue()
    : capacity(1024), wb(WriteBlock), rb(ReadBlock) {
      std::srand(std::time(nullptr));
    }

  //! Constructs a queue with specified \p capacity and read / write behaviors
  Queue(size_t capacity,
        WriteBehavior wb = WriteBlock, ReadBehavior rb = ReadBlock)
    : capacity(capacity), wb(wb), rb(rb) {
      std::srand(std::time(nullptr));
    }

  //! Makes a copy of \p item and pushes it to the front of the queue
  void push_front(const T &item) {
    std::unique_lock<std::mutex> lock(q_mutex);
    while (!is_not_full()) {
      if (wb == WriteReturn) return;
      q_not_full.wait(lock);
    }
    queue.push_front(item);
    lock.unlock();
    q_not_empty.notify_one();
  }

  //! Moves \p item to the front of the queue
  void push_front(T &&item) {
    std::unique_lock<std::mutex> lock(q_mutex);
    while (!is_not_full()) {
      if (wb == WriteReturn) return;
      q_not_full.wait(lock);
    }
    queue.push_front(std::move(item));
    std::cout << "push " << item << std::endl;
    lock.unlock();
    q_not_empty.notify_one();
  }

  // flag = 0, buffer the packet, flag = 1, normal packet
  void push_front_adv(const T &item, bool flag) {
    std::unique_lock<std::mutex> lock(q_mutex);
    if (flag) {
      while (!is_not_full()) {
        if (wb == WriteReturn) return;
        q_not_full.wait(lock);
      }
      queue.push_front(std::move(item));
      std::cout << "org push " << item << std::endl;
    }
    else{
      while (!is_not_full_buf()) {
        if (wb == WriteReturn) return;
        q_not_full_buf.wait(lock);
      }
      queue_buf.push_front(std::move(item));
      std::cout << "buf push " << item << std::endl;
    }
    lock.unlock();
    q_not_empty.notify_one();
  }

  //! Pops an element from the back of the queue: moves the element to `*pItem`.
  void pop_back(T* pItem) {
    std::unique_lock<std::mutex> lock(q_mutex);
    while (!is_not_empty())
      q_not_empty.wait(lock);
    *pItem = std::move(queue.back());
    queue.pop_back();
    std::cout << "pop " << *pItem << std::endl;
    lock.unlock();
    q_not_full.notify_one();
  }

  void pop_back_adv(T* pItem) {
    std::unique_lock<std::mutex> lock(q_mutex);
    while (!is_not_empty_all())
      q_not_empty.wait(lock);
    //std::cout << "clock: " << std::clock_t() << std::endl;
    if ((std::rand() % 10) == 0) {
      if (is_not_empty_buf()){
        *pItem = std::move(queue_buf.back());
        queue_buf.pop_back();
        std::cout << "buf pop " << *pItem << std::endl;
      }
    }
    else{
      if (is_not_empty()){
        *pItem = std::move(queue.back());
        queue.pop_back();
        std::cout << "org pop " << *pItem << std::endl;
      }
    }
    lock.unlock();
    q_not_full.notify_one();
  }

  //! Get queue occupancy
  size_t size() const {
    std::unique_lock<std::mutex> lock(q_mutex);
    return queue.size();
  }

  size_t get_capacity() {
    //std::unique_lock<std::mutex> lock(q_mutex);
    return capacity;
  }

  //! Change the capacity of the queue
  void set_capacity(const size_t c) {
    // change capacity but does not discard elements
    std::unique_lock<std::mutex> lock(q_mutex);
    capacity = c;
  }

  //! Deleted copy constructor
  Queue(const Queue &) = delete;
  //! Deleted copy assignment operator
  Queue &operator =(const Queue &) = delete;

  //! Deleted move constructor (class includes mutex)
  Queue(Queue &&) = delete;
  //! Deleted move assignment operator (class includes mutex)
  Queue &&operator =(Queue &&) = delete;

 private:
  bool is_not_empty() const { return queue.size() > 0; }
  bool is_not_full() const { return queue.size() < capacity; }
  bool is_not_empty_buf() const { return queue_buf.size() > 0; }
  bool is_not_full_buf() const { return queue_buf.size() < capacity; }
  bool is_not_empty_all() const { return queue.size() + queue_buf.size() > 0; }
  bool is_not_full_all() const { return (queue.size() < capacity) && (queue_buf.size() < capacity); }

  size_t capacity;
  std::deque<T> queue;
  std::deque<T> queue_buf;
  WriteBehavior wb;
  ReadBehavior rb;

  mutable std::mutex q_mutex;
  mutable std::condition_variable q_not_empty;
  mutable std::condition_variable q_not_full;
  mutable std::condition_variable q_not_full_buf;
};

class Switch {
  public:
    Switch(int max_size = 1024):input_buffer(2048)
    {
      size = max_size;
      std::srand(std::time(nullptr));
    };

    void add_packet(int x)
    {
      std::this_thread::sleep_for(std::chrono::milliseconds(1000));
      input_buffer.push_front(x);
      //std::cout << "push " << x << std::endl;
      //std::cout << x << std::endl;
    };

    void test_packet()
    {
      //for (i=0; i<100; i++)
      //{
      //  input_buffer.push_front(i);
      //}
      std::this_thread::sleep_for(std::chrono::milliseconds(1000));
      input_buffer.push_front_adv(5, true);
      std::this_thread::sleep_for(std::chrono::milliseconds(2000));
      //std::cout << "push 5" << std::endl;
      input_buffer.push_front_adv(3, false);
      std::this_thread::sleep_for(std::chrono::milliseconds(1000));
      //std::cout << "push 3" << std::endl;
      input_buffer.push_front_adv(10, false);
      //std::cout << "push 10" << std::endl;
    };

    void pop_packet(int * x, int y)
    {
      while (y > 0)
      {
        input_buffer.pop_back_adv(x);
        //std::cout << "pop" << *x << std::endl;
        //std::cout << *x << std::endl;
        y = y - 1;
      }
    };

    int get_capacity()
    {
      return input_buffer.get_capacity();
    }

    void rand_test(){
        std::cout << std::rand() % 10 << std::endl;
    }

  private:
    Queue<int> input_buffer;
    int size;
};



int main()
{
  //Queue<int> input_buffer(8);
  //std::cout << input_buffer.get_capacity() << std::endl;
  Switch sw;
  //std::cout << sw.get_capacity() << std::endl;
  int y = 0;
  int * x = &y;
  //sw.add_packet(5);
  //sw.pop_packet(x);
  //std::cout << *x << std::endl;

  //std::thread t1(&Switch::add_packet, &sw, 10);

  //std::thread t1(&Switch::test_packet, &sw);


  //std::thread t2(&Switch::pop_packet, &sw, x, 3);
  //t1.join();
  //t2.join();

  std::cout << *x << std::endl;

  for (int i=0; i<10; i++){
    sw.rand_test();
  }

  //std::unique_ptr<int> packet;
  //if (packet == nullptr) std::cout << "ri" << std::endl;


  std::cout << "haha" << std::endl;
}
