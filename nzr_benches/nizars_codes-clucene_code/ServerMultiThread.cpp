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
#include <fcntl.h>
#include <netdb.h>
#include <errno.h>
#include <arpa/inet.h>
#include <chrono>
#include <ctime>
#include "tbb/concurrent_queue.h"
#include "tbb/concurrent_unordered_map.h"
#include "tbb/tick_count.h"

using namespace std;
using namespace chrono;
using namespace tbb;
using namespace lucene::util;
using namespace lucene::analysis;
using namespace lucene::index;
using namespace lucene::queryParser;
using namespace lucene::document;
using namespace lucene::search;
using namespace lucene::store;

#define MAXBUF 500
#define MAXEVENTS 64

struct QueryDelay {
    chrono::time_point<std::chrono::system_clock> queueDelayStart;
    chrono::time_point<std::chrono::system_clock> queueDelayEnd;
    chrono::time_point<std::chrono::system_clock> searchDelayStart;
    chrono::time_point<std::chrono::system_clock> searchDelayEnd;
};

tbb::concurrent_queue<string> request_queue;
tbb::concurrent_unordered_map<string, QueryDelay> queryQueLat;
static int socket_fd, epoll_fd;
//unordered_map<string, QueryDelay> queryQueLat;

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
 
 cout << "Experiment done. Writing log now." << endl;

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

static int make_socket_non_blocking(int sfd)
{
    int flags;
    
    // get the status flag of @sfd
    flags = fcntl(sfd, F_GETFL, 0);
    if (flags == -1) {
        perror("fcntl");
        return -1;
    }
    
    // add the non-blocking flag to the current flag
    flags |= O_NONBLOCK;
    if (fcntl(sfd, F_SETFL, flags) == -1) {
        perror("fcntl");
        return -1;
    }

    return 0;
}

void accept_and_add_new()
{
    struct epoll_event event;
    struct sockaddr in_addr;
    socklen_t in_len = sizeof(in_addr);
    int infd;
    char hbuf[NI_MAXHOST], sbuf[NI_MAXSERV];

    while ((infd = accept(socket_fd, &in_addr, &in_len)) != -1) {

        if (getnameinfo(&in_addr, in_len,
                hbuf, sizeof(hbuf),
                sbuf, sizeof(sbuf),
                NI_NUMERICHOST | NI_NUMERICHOST) == 0) {
            printf("Accepted connection on descriptor %d (host=%s, port=%s)\n",
                    infd, hbuf, sbuf);
        }
        /* Make the incoming socket non-block
         * and add it to list of fds to
         * monitor*/
        if (make_socket_non_blocking(infd) == -1) {
            abort();
        }

        event.data.fd = infd;
        event.events = EPOLLIN | EPOLLET;
        if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, infd, &event) == -1) {
            perror("epoll_ctl");
            abort();
        }
        in_len = sizeof(in_addr);
    }

    if (errno != EAGAIN && errno != EWOULDBLOCK)
        perror("accept");
    /* else
     *
     * We hae processed all incomming connectioins
     *
     */
}

static void socket_create_bind_local()
{
    struct sockaddr_in server_addr;
    int opt = 1;

    if ((socket_fd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
        perror("Socket");
        exit(1);
    }
    
    // int setsockopt(int sockfd, int level, int optname, const void *optval, socklen_t optlen);
    // SOL_SOCKET: When manipulating socket options, the level at which the option resides and the name of the option must be specified.
    // To manipulate options at the sockets API level, level is specified as SOL_SOCKET.
    // SO_REUSEADDR: 
    // The arguments optval and optlen are used to access option values
    if (setsockopt(socket_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(int)) == -1) {
        perror("Setsockopt");
        exit(1);
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(portno);
    inet_aton(SERVER_IP, &server_addr.sin_addr);
    
    // Most of the net code does not use sockaddr_in, it uses sockaddr. When you use a function like sendto, 
    // you must explicitly cast sockaddr_in, or whatever address you are using, to sockaddr. 
    // sockaddr_in is the same size as sockaddr, but internally the sizes are the same because of a slight hack.
    // That hack is sin_zero. Really the length of useful data in sockaddr_in is shorter than sockaddr. 
    // But the difference is padded in sockaddr_in using a small buffer; that buffer is sin_zero.
    bzero(&(server_addr.sin_zero), 8);

    if (bind(socket_fd, (struct sockaddr *)&server_addr, sizeof(struct sockaddr))
                                                                   == -1) {
        perror("Unable to bind");
        exit(1);
    }
}


void process_new_data(int fd, ofstream& queueStartLogFile)
{
    ssize_t count;
    char buf[512];

    while ((count = read(fd, buf, sizeof(buf) - 1))) {
        if (count == -1) {
            /* EAGAIN, read all data */
            if (errno == EAGAIN)
                return;

            perror("read");
            break;
        }

        /* Write buffer to stdout */
        buf[count] = '\0';
        //printf("From client: %s \n", buf);
        puts(buf);

        string queries = string(buf);
        queries.erase(queries.find_last_not_of("$$") + 1);

        std::stringstream ss(queries);
        char delim = '$$';
        string queryString;
        while (std::getline(ss, queryString, delim)) {
            // get query tag
            string queryTag = queryString.substr(0, queryString.find(" **"));
            QueryDelay queryDelay;
            queryDelay.queueDelayStart = chrono::system_clock::now();
            //queryQueLat[queryTag] = queryDelay;
            
            
            chrono::milliseconds ms = duration_cast< milliseconds >(
                        system_clock::now().time_since_epoch()
                    );
            queueStartLogFile << queryTag << "," << ms.count() << endl;
            string queryStringSid = queryString + " SID" + std::to_string(fd);
            request_queue.push(queryStringSid);
        }
    }

    printf("Close connection on descriptor: %d\n", fd);
    close(fd);
}

/* Get requests (search keyword) from client and add them to
 * the concurrent queue.
 * */
void get_request()
{
    string queueStartLogName = string("Server_Queue_Start_") + string(SERVER_ID) + string(".log");
    ofstream queueStartLogFile(queueStartLogName);

    struct epoll_event event, *events;

    socket_create_bind_local();

    if (make_socket_non_blocking(socket_fd) == -1)
        exit(1);

    if (listen(socket_fd, 5) == -1) {
        perror("Listen");
        exit(1);
    }

    printf("\nTCPServer Waiting for client on port %d\n", portno);
        fflush(stdout);

    epoll_fd = epoll_create1(0);
    if (epoll_fd == -1) {
        perror("epoll_create1");
        exit(1);
    }

    event.data.fd = socket_fd;
    event.events = EPOLLIN;
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, socket_fd, &event) == -1) {
        perror("epoll_ctl");
        exit(1);
    }

    events = (epoll_event*)calloc(MAXEVENTS, sizeof(event));
    
    while(1) {
        int n, i;

        if (complete_flag == true) {
         break;
        }

        n = epoll_wait(epoll_fd, events, MAXEVENTS, -1);

        for (i = 0; i < n; i++) {
            tick_count currentTime = tick_count::now();

            if (complete_flag == true) {
              break;
            }
            
            if (events[i].events & EPOLLERR || events[i].events & EPOLLHUP ||
                !(events[i].events & EPOLLIN)) {
                /* An error on this fd or socket not ready */
                perror("epoll error");
                close(events[i].data.fd); } 
            else if (events[i].data.fd == socket_fd) { // 
                /* New incoming connection */
                accept_and_add_new();
            } else {
                /* Data incoming on fd */
                process_new_data(events[i].data.fd, queueStartLogFile);
            }
        }
    }

    free(events);
    close(socket_fd);
}

void searcher_contents() {
  standard::StandardAnalyzer analyzer;
  TCHAR tterms[500];
  thread::id myid = this_thread::get_id();
  stringstream ss; ss << myid;
  string log_fn = string("Server_") + string(SERVER_ID) + string("_Verbose_log_") + ss.str() + string(".log");
  string searchStartLogName = string("Server_Search_Start_") + string(SERVER_ID) + "_"  + ss.str() + string(".log");
  string searchEndLogName = string("Server_Search_End_") + string(SERVER_ID) + "_"  + ss.str() + string(".log");
  string queryLogName = string("Server_Query_") + string(SERVER_ID) + "_"  + ss.str() + string(".log");
  string queueEndLogName = string("Server_Queue_End_") + string(SERVER_ID) + "_"  + ss.str() + string(".log");
  // TODO: need create a log file per thread. one line per query
  //ofstream verboseLogFile(log_fn);
  ofstream searchStartLogFile(searchStartLogName);
  ofstream searchEndLogFile(searchEndLogName);
  ofstream queryLogFile(queryLogName);
  ofstream queueEndLogFile(queueEndLogName);
  //verboseLogFile << "open index files " << endl;
  Directory * dir = FSDirectory::getDirectory(INDEX_FILE_DIR);
  IndexReader* reader = IndexReader::open(dir);
  
  //verboseLogFile << "open indexfile done " << endl;
 
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
   //QueryDelay queryDelay = queryQueLat[queryTag];
   //queryDelay.queueDelayEnd = tick_count::now();
   //queryQueLat[queryTag].queueDelayEnd = chrono::system_clock::now();
   //verboseLogFile << "Request popped from queue: " << buf.c_str() << endl;
   // Query is in this format: QueryTag + " **" + term + " **" + phrase
    
    queryLogFile << queryTag << endl;
    
    chrono::milliseconds ms = duration_cast< milliseconds >(
                 system_clock::now().time_since_epoch()
             );
    queueEndLogFile << queryTag << ", " << ms.count() << endl; 

    string terms_str = buf.substr(buf.find(" **") + 3, buf.substr(buf.find(" **") + 3).length() - buf.substr(buf.rfind(" **")).length()); // get term
    
    // Get the socket id
    string sock_fd = buf.substr(buf.find(" SID") + 4, buf.length());
    //cout << "Terms:" << terms_str << endl << "SID: " << sock_fd << endl;
    
    // todo: delete this line 
    queryTag = buf.substr(0, buf.find(" **")); // get query tag

    string phrase = buf.substr(buf.rfind(" **") + 3, buf.substr(buf.rfind(" **") + 3).length() - buf.substr(buf.find(" SID")).length()); // get phrase

    //verboseLogFile << "\n**************** Query#" << icount << " ***********************" << endl;   
    //verboseLogFile << "\n\n" << icount << ") Query: "  << terms_str << endl;
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
    //queryQueLat[queryTag].searchDelayStart = chrono::system_clock::now();
    chrono::milliseconds ms1 = duration_cast< milliseconds >(
                system_clock::now().time_since_epoch()
            );
     
    searchStartLogFile << queryTag << "," << ms1.count() << endl;
    // get the search result given the query object
    Hits* h = s.search(q);
    
    chrono::milliseconds ms2 = duration_cast< milliseconds >(
                system_clock::now().time_since_epoch()
             ); 
    searchEndLogFile << queryTag << "," << ms2.count() << endl;
    //queryQueLat[queryTag].searchDelayEnd = chrono::system_clock::now();    
    
    vector<string> result;
   
    // return TOPK only
    int topk = min(TOPK, (int)h->length());
    if (topk > 0) {
        // " **" after the queryTag means that there is search result
        sendToClient << "\n\n" << queryTag << " **" << endl;
        sendToClient << "  Query: "  << terms_str << endl; 
         
        //verboseLogFile << "  Showing search result for top " << topk << " documents: " << endl;
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
          //verboseLogFile << "     "  << i + 1 << ". " << path << endl;
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
       

        //verboseLogFile << "Search took(us): " << time_elapsed << endl;
        sendToClient << "\nSearch took(us): " << time_elapsed << endl;
        
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

  //verboseLogFile.close();
  searchStartLogFile.close();
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
     //workers.push_back(thread(search_function));
     workers.push_back(thread(searcher_contents));
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
  
  //logQueryDelay();

  return 0;
}
