#include "CLucene/StdHeader.h"
#include "CLucene/_clucene-config.h"

#include "CLucene.h"
#include "CLucene/util/Misc.h"
#include "CLucene/store/FSDirectory.h"
#include "CLucene/store/RAMDirectory.h"
#include "CLucene/store/Directory.h"
#include "CLucene/config/repl_tchar.h"
#include "CLucene/config/repl_wchar.h"

#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <thread>
#include <sstream>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <unordered_map>
#include <sys/types.h> 
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/epoll.h>
#include <arpa/inet.h>
#include <chrono>
#include <ctime>
#include "tbb/concurrent_queue.h"
#include "tbb/tick_count.h"

using namespace std;
using namespace tbb;
using namespace lucene::util;
using namespace lucene::analysis;
using namespace lucene::index;
using namespace lucene::queryParser;
using namespace lucene::document;
using namespace lucene::search;
using namespace lucene::store;

#define MAXBUF 500
/*
struct QueryDelay {
 tick_count queueDelayStart;
 tick_count queueDelayEnd;
 tick_count searchDelayStart;
 tick_count seachDelayEnd;
};*/

struct QueryDelay {
    chrono::time_point<std::chrono::system_clock> queueDelayStart;
    chrono::time_point<std::chrono::system_clock> queueDelayEnd;
    chrono::time_point<std::chrono::system_clock> searchDelayStart;
    chrono::time_point<std::chrono::system_clock> searchDelayEnd;
};




tbb::concurrent_queue<string> request_queue;

unordered_map<string, QueryDelay> queryQueLat;

char* INDEX_FILE_DIR = "./index_original_compressed/";
char* SERVER_ID;
char* SERVER_IP;
int portno;
int NO_OF_CLIENT;
int numThreads;
int TOPK;
const int QUEUE_LEN = 36;
int TEST_TIME_LEN = 10 * 60;
bool complete_flag = false;

int QueryCount = 0;

void error(const char *msg)
{
    perror(msg);
    exit(1);
}

void logQueryDelay() {
 time_t t = std::time(0);
 long int timestamp = static_cast<long int> (t);

 string log_fn = string("Server_") + string(SERVER_ID) + string("_Search_Queue_Delay") + string(".csv");
 ofstream queueLogFile(log_fn);
 queueLogFile << "QueryTag," << "Queue Latency(us)," << "SearchLatency(us)" << endl;
 for (auto it = queryQueLat.begin(); it != queryQueLat.end(); ++it) {
     chrono::duration<double> queue_lat = it->second.queueDelayEnd - it->second.queueDelayStart;
     chrono::duration<double> search_lat = it->second.searchDelayEnd - it->second.searchDelayStart;         
     
     queueLogFile << it->first << ", " << queue_lat.count() * 1000000 << ", " << search_lat.count() * 1000000 << endl; // in microsecond
     
     // for deugging
     std::time_t ttp_start = std::chrono::system_clock::to_time_t(it->second.queueDelayStart);
     std::time_t ttp_end = std::chrono::system_clock::to_time_t(it->second.queueDelayEnd);
     //queueLogFile << it->first  << " " << ctime(&ttp_start) << " " <<  ctime(&ttp_end) << endl;
 }
}

/* Get requests (search keyword) from client and add them to
 * the concurrent queue.
 * */
void get_request()
{
    socklen_t clilen;
    char buffer[MAXBUF];
    struct sockaddr_in serv_addr, cli_addr;
    int n;
    
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) 
        error("ERROR opening socket");
    bzero((char *) &serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    inet_aton(SERVER_IP, &serv_addr.sin_addr);
    serv_addr.sin_port = htons(portno);
    if (bind(sockfd, (struct sockaddr *) &serv_addr,
        sizeof(serv_addr)) < 0) 
        error("ERROR on binding");
    listen(sockfd, 1000);
    
    // the following code is for epoll 
    // *******************************************************************************
    //  events is an array of epoll_event structures. evlist is allocated by the calling
    //  process and when epoll_wait returns, this array is modified to indicate information 
    //  about the subset of file descriptors in the interest list that are in the ready state 
    //  (this is called the ready list)
    struct epoll_event events[5];
   
    // epoll_create: creates a context, parameter is ignored but has to be positive.
    // previously the param was used to let kernel know about possible number
    // of file descriptors
    int epfd = epoll_create(1);
 
    //  add file descriptors to the context, i.e. start monitoring the socket for events
    // The server will wait till there are NO_OF_CLIENT number of clients are connected
    for (int i = 0; i < NO_OF_CLIENT; i++) 
    {
       // create an epoll_event, this event is associated with a connection
       static struct epoll_event ev;
       memset(&cli_addr, 0, sizeof (cli_addr));
       clilen = sizeof(cli_addr);

       // when a client connects to the server, set the created event's file
       // descriptor as this one
       ev.data.fd = accept(sockfd,(struct sockaddr*)&cli_addr, &clilen);
       if (ev.data.fd >= 0) {
        cout << "Server got connected with client" << endl;
       } 
       // set the event type 
       ev.events = EPOLLIN;
        
       // start watching the event by adding it to the interest list
       epoll_ctl(epfd, EPOLL_CTL_ADD, ev.data.fd, &ev); 
   }
 
  int nfds;
  // this loop will keep running and check which fds became active
  while(1) {
    // epoll_wait() returns how many fd became active
  	// epoll_wait(int epfd, struct epoll_event *evlist, int maxevents, int timeout);
    // maxevents: length of evlist
    // timeout: how long epoll_wait will block
    nfds = epoll_wait(epfd, events, 5, 0);
    
    // loop over the active fds    
	for(int i = 0; i < nfds;i++) {
		// get (read) request from client	
        memset(buffer,0,MAXBUF);
        read(events[i].data.fd, buffer, MAXBUF);
        puts(buffer);
        
        string queryString = string(buffer);
        string queryTag = queryString.substr(0, queryString.find(" **")); // get query tag

        QueryDelay queryDelay;
        //queryDelay.queueDelayStart = tick_count::now();
        queryDelay.queueDelayStart = chrono::system_clock::now();
        queryQueLat[queryTag] = queryDelay;
        
        request_queue.push(queryString + " SID" + std::to_string(events[i].data.fd));
	}

    if (complete_flag == true) {
        cout << "worker: complete flag true, finish now" << endl;
        sleep(5);
        logQueryDelay();
        break;
    }
  } 
     
  close(sockfd);
  return; 
}

void searcher_contents() {
  standard::StandardAnalyzer analyzer;
  TCHAR tterms[500];
  thread::id myid = this_thread::get_id();
  stringstream ss; ss << myid;
  string log_fn = string("Server_") + string(SERVER_ID) + string("_Verbose_log_") + ss.str() + string(".log");
  string processLogName = string("Server_") + string(SERVER_ID)  + string("_log_") + ss.str() + string(".log");
 
  // TODO: need create a log file per thread. one line per query
  ofstream verboseLogFile(log_fn);
  ofstream processLogFile(processLogName);
  verboseLogFile << "open index files " << endl;
  Directory * dir = FSDirectory::getDirectory(INDEX_FILE_DIR);
  IndexReader* reader = IndexReader::open(dir);
  
  verboseLogFile << "open indexfile done " << endl;
  
  unsigned long long icount = 0;
  while (true) {
    if (complete_flag == true) {
        cout << "worker: complete flag true, finish now" << endl;
        sleep(5);
        break;
    }
    
    // "buf" will contain query string (sent by client) ++ socket id (of the 
    // socket that is connecting client and server)
    string buf;
    request_queue.try_pop(buf);
    if(strlen(buf.c_str()) == 0) {
      usleep(2000);
      continue; 
    }
   
   // find out the time a query spend in the queue
   string queryTag = buf.substr(0, buf.find(" **")); // get query tag 
   QueryDelay queryDelay = queryQueLat[queryTag];
   //queryDelay.queueDelayEnd = tick_count::now();
   queryQueLat[queryTag].queueDelayEnd = chrono::system_clock::now();
   verboseLogFile << "Request popped from queue: " << buf.c_str() << endl;
   // Query is in this format: QueryTag + " **" + term + " **" + phrase
    
    string terms_str = buf.substr(buf.find(" **") + 3, buf.substr(buf.find(" **") + 3).length() - buf.substr(buf.rfind(" **")).length()); // get term
    
    // Get the socket id
    string sock_fd = buf.substr(buf.find(" SID") + 4, buf.length());
    cout << "Terms:" << terms_str << endl << "SID: " << sock_fd << endl;
    
    // todo: delete this line 
    queryTag = buf.substr(0, buf.find(" **")); // get query tag

    string phrase = buf.substr(buf.rfind(" **") + 3, buf.substr(buf.rfind(" **") + 3).length() - buf.substr(buf.find(" SID")).length()); // get phrase

    //verboseLogFile << "\n**************** Query#" << icount << " ***********************" << endl;   
    verboseLogFile << "\n\n" << icount << ") Query: "  << terms_str << endl;
    // TODO may not need to declare a IndexSearcher everytime. Need fine tune.

    // a new string stream that will contain search result of the current query
    stringstream sendToClient;
    //sendToClient << "\n**************** Query#" << icount << " ***********************" << endl;
    
    IndexSearcher s(reader);
    
    STRCPY_AtoT(tterms, terms_str.c_str(), terms_str.size());
    tterms[terms_str.size()] = '\0';
    //std::wcout << myid << " query:" << tterms <<  " icount: " << icount << endl;
    
    //  construct Query object from the user-given query
    Query* q = QueryParser::parse(tterms, _T("contents"), &analyzer); // NOTE: special chars may cause seg fault and can't include "and", "or", "not" after "+"
    
    tick_count t0 = tick_count::now();
    queryQueLat[queryTag].searchDelayStart = chrono::system_clock::now();
    // get the search result given the query object
    Hits* h = s.search(q); 
    queryQueLat[queryTag].searchDelayEnd = chrono::system_clock::now();    
    vector<string> result;
   
    // return TOPK only
    int topk = min(TOPK, (int)h->length());
    if (topk > 0) {
        // " **" after the queryTag means that there is search result
        sendToClient << "\n\n" << queryTag << " **" << endl;
        sendToClient << "  Query: "  << terms_str << endl; 
         
        verboseLogFile << "  Showing search result for top " << topk << " documents: " << endl;
        sendToClient << "  Showing search result for top " << topk << " documents: " << endl;

        // iterate over the topk hits and get the corresponding documents
        for ( size_t i = 0; i < topk; i++ ) {
          Document* doc = &h->doc(i);
          //const TCHAR* content =  doc->get(_T("contents"));
          //TCHAR* content =  doc->toString();
          //vc.push_back(content);
          
          // wchar_t is 16 bit or 32 bit wide (platform-dependent), char is 8 bit. 
          // It is used for unicode characters.
          // _T stands for “text”. It will turn your literal into a Unicode wide character 
          // literal if and only if you are compiling your sources with Unicode support.
          const wchar_t* wpath = doc->get(_T("path"));
          auto e = wcslen(wpath); // 
          char path[e];
          std::wcstombs(path, wpath, e); // wide-character string to multibyte string of char type
        
          //verboseLogFile << "Path: " << path << ", score: " << h->score(i) << endl;
          //verboseLogFile << i << ". " << doc->get(_T("path")) << "-" << h->score(i) << endl;
          verboseLogFile << "     "  << i + 1 << ". " << path << endl;
          sendToClient <<   "     "  << i + 1 << ". " << path << endl;
          
          // get and print the content
          const wchar_t* wcontents = doc->get(_T("contents"));
          e = wcslen(wcontents);
          char contents[e];
          std::wcstombs(contents, wcontents, e);
          //verboseLogFile << "Content: " << contents << "\n" <<endl;
        } // topk document loop end
         
        tick_count t1 = tick_count::now();

        double time_elapsed = (t1 - t0).seconds() * 1000000.0;
       

        verboseLogFile << "Search took(us): " << time_elapsed << endl;
        sendToClient << "\nSearch took(us): " << time_elapsed << endl;
        //processLogFile << queryTag << " SearchLatency " << time_elapsed << " us" << " QueueLatency " << endl; 
        
        // first send the size of the message so Client can allocate enough memory
        uint32_t dataLength = htonl(sendToClient.str().length()); // ensure network byte order
        //write(stoi(sock_fd), &dataLength, sizeof(uint32_t));
        
        // write(stoi(sock_fd), buffer, MAXBUF);
    } // if
    else {
       sendToClient << "\n\n"  << queryTag << endl;
       sendToClient << "  Query: "  << terms_str << endl;
       sendToClient << "  No result" << endl;
    }    
    // Now, send the actual data, i.e. search results
    write(stoi(sock_fd), sendToClient.str().c_str(), sendToClient.str().length());
    
    _CLLDELETE(h);	
    _CLLDELETE(q);

    s.close();
    icount++;
  }

  verboseLogFile.close();
  processLogFile.close();
  reader->close();
  _CLLDELETE(reader);
}


int main(int argc, char* argv[])
{
  // make sure the number of arguments are correct
  if (argc != 9) { 
    printf("Usage: %s thread_number run_time(min) topk test_name(t, c, tc, tpc) serverIp serverId portNo noOfClient\n", argv[0]);
    exit(0);
  }

  // populate the variables with arguments 
  numThreads = atoi(argv[1]);
  TEST_TIME_LEN = 60 * atoi(argv[2]);
  TOPK = atoi(argv[3]);
  string test_name = argv[4];
  SERVER_IP = argv[5];
  SERVER_ID = argv[6];
  portno = atoi(argv[7]);
  NO_OF_CLIENT = atoi(argv[8]);

  cout << "numThreads: " << numThreads << " test for " << TEST_TIME_LEN << "TopK value: " << TOPK << " seconds" << endl;
  
  // declare a function pointer which doesnot take any arguments (void)
  // and returns nothing (void)
  void (*search_function)(void);

  // based on the test name the function pointer will point to a function 
  if (!(test_name.compare("t"))) {
     //search_function = &searcher_title; 
  } else if (!(test_name.compare("c"))) {
     search_function = &searcher_contents;
  } else if (!(test_name.compare("tc"))) {
     //search_function = &searcher_title_contents;
  } else if (!(test_name.compare("tpc"))) {
     //search_function = &searcher_title_phrased_contents;
  } else if (!(test_name.compare("tct"))) {
     //search_function = &searcher_title_contents_time;
  } else {
    printf("\n\nError: test_name not valid (\"t\" for title, \"c\" for contents, \"tc\" for title & contents, \"tpc\" for title phrased and contents, \"tct\" for title & contents sorted by time)\n\n\n");
    exit(0);
  }

  thread t0(get_request);
  vector<thread> workers;

  for (int i = 0; i < numThreads; i++) {
     workers.push_back(thread(search_function));
  }

  tick_count time0 = tick_count::now();
 
  while(true) {
    tick_count time1 = tick_count::now(); 
    if((time1 - time0).seconds() < TEST_TIME_LEN) {
        sleep(8);
    }
    else {
        complete_flag = true;
        break;
    }
  }
  
  for(auto &t : workers) {
    t.join();
  }
  t0.join();
   
  return 0;
}
