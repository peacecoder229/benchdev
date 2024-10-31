#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h> 
#include <iostream>
#include <fstream>
#include <sstream>
#include <string.h>
#include <time.h>
#include <ctime>
#include <vector>
#include <string>
//#include "tbb/tick_count.h"
#include <chrono>
#include <arpa/inet.h>

using namespace std;
//using namespace tbb;

const char* portFile = "port_file";
const char* termQueryFile = "term_query_file";
const char* phraseQueryFile = "phrase_query_file";

string ClientNo;
char* SERVER_IP;

#define MAXBUF 2000

void error(const char *msg)
{
    perror(msg);
    exit(0);
}


/* Reads the query string from the files, puts them in a vector<string>
 * then return the vector<string>
 * */
vector<string> generate_requests()
{
  string termQueryFileName = string(termQueryFile) + "_" + ClientNo;
  fstream infile_term(termQueryFileName);  
  if (infile_term.fail()) {
    infile_term.open(termQueryFile);

    if (!infile_term.is_open()) {
      printf("Error: phrase query file doesn't exist, exit now\n");
    }
  }

  string phraseQueryFileName = string(phraseQueryFile) + "_" + ClientNo; 
  ifstream infile_phrase(phraseQueryFileName);
  if(infile_phrase.fail()) {
    infile_phrase.open(string(phraseQueryFile));

    if(!infile_phrase.is_open()) {
      printf("Error: phrase query file doesn't exist, exit now\n");
    }
  }
  
  // this container has the requests from termQueryFile and
  // termPhraseFile. Each item of the container is in this format
  // term ++phrase
  vector<string> all_requests;
  
  // no used anywhere 
  vector<unsigned int> ireq_vec;

  // populate all_requests
  string line_term;
  string line_phrase;
  int queryCount = 1;
  while(getline(infile_term,line_term) && 
     getline(infile_phrase, line_phrase)) {
     string queryTag = string("Client_") + ClientNo + string("_") + string("Query_") + to_string(queryCount);
     //all_requests.push_back(ClientNo + " **" + line_term + " **" + line_phrase);
     all_requests.push_back( queryTag + " **" + line_term + " **" + line_phrase + "$$");
     //cout << "Adding query: " << line_term + " ++" + line_phrase << endl;
     queryCount++;
  }

  return all_requests;
}

int main(int argc, char *argv[])
{
    char buffer[MAXBUF];

    SERVER_IP = argv[1];
    int portno = atoi(argv[2]);
    ClientNo = string(argv[3]);
    
    // get the request from the file
    vector<string> all_requests = generate_requests();
    
    // make sure correct number of arguments are provided.  
    if (argc < 3) {
       fprintf(stderr,"usage %s hostname port clientId\n", argv[0]);
       exit(0);
    }
    
    // set up the logging
    time_t t = std::time(0);
    long int timestamp = static_cast<long int> (t);
    string log_fn = string("Client_RTT_") + string(argv[3]) + string(".csv");
    ofstream rttLog(log_fn);
    
    // create a socket
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) 
        error("ERROR opening socket");
    
    // populate the hostent struct "server" with IP 
    struct hostent *server = gethostbyname(argv[1]);
    if (server == NULL) {
        fprintf(stderr,"ERROR, no such host\n");
        exit(0);
    }
   
    // serv_addr will have the server IP and port number 
    struct sockaddr_in serv_addr;
    bzero((char *) &serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    bcopy((char *)server->h_addr, 
         (char *)&serv_addr.sin_addr.s_addr,
         server->h_length); // copy server IP to serv_addr
    inet_aton(SERVER_IP, &serv_addr.sin_addr);
    //serv_addr.sin_addr = inet_addr("192.168.1.99");
    serv_addr.sin_port = htons(portno); // set port no to serv_addr
    
    bool isServerOnline = false;
    // connect to the server using socket file decriptor and serv_addr
    if (connect(sockfd,(struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) { 
        struct sockaddr_in* pV4Addr = (struct sockaddr_in*)&serv_addr;
        struct in_addr ipAddr = pV4Addr->sin_addr;
        char str[INET_ADDRSTRLEN];
        inet_ntop( AF_INET, &ipAddr, str, INET_ADDRSTRLEN );
        
        cout << "Error connecting to server: " << str << endl;
	error("ERROR connecting");
    }
    else {
       cout << "Client#" << argv[3] << " got connected to server at socket" << sockfd  << endl;
       isServerOnline = true; 
    }
     
    // enter the loop and keep sending requests, and receiving response 
    ofstream searchResult; // for writing search result to file
    string resultFileName = string("Search_result_") + string(argv[3]) + string(".txt");
    searchResult.open(resultFileName);
    
    unsigned queryNo = 1; // used for logging
    unsigned i = 0; 
    while(true) {
        // when i =  all_requests.size() - 10 + 1, reset i to 0
        // it makes sure the client keep sending requests as long
        // as server is online 
        if (i > all_requests.size() - 10) {
            i = 0;
        }

        // why do you need the sleeping time?
        //usleep(30000);
        //  usleep(1000);
        // why this magic number 
        if(strlen(all_requests[i].c_str()) > 500) {
            printf("request buffer larger than 500, continuing\n");
            continue;
        }
        
        // take a note of the sending time 
        // tick_count sendingTime = tick_count::now();
        std::chrono::time_point<std::chrono::system_clock> sendingTime = std::chrono::system_clock::now();

        // Send(write) the query to the server 
        //printf("Client#%s: Sending %s\n", argv[3], all_requests[i].c_str());
        if (write(sockfd, all_requests[i].c_str(), 
                  strlen(all_requests[i].c_str())) < 0) {
            error("ERROR writing to socket");   
           isServerOnline = false; 
        }
      
        // Recive(read) response from server
        // First receive data length and allocate that much memory
        //uint32_t dataLength;
        // if (read(sockfd, &datalength, sizeof(uint32_t)))  
        memset(buffer, 0, MAXBUF); 
        if (read(sockfd, buffer, MAXBUF) < 0) {
          isServerOnline = false;
          break;
        }
        else {
           //dataLength = ntohl(dataLength);
           // puts(buffer);
        }

        // take a note of the receiving time.
        // tick_count receivingTime;
       
        double rtt;

		if (isServerOnline) {
           //std::vector<uint8_t> rcvBuf;    // Allocate a receive buffer
           // rcvBuf.resize(dataLength,0x00); // with the necessary size
            
            // receive data (search result)
            //read(sockfd, &(rcvBuf[0]), dataLength);
            //std::string receivedString; // assign buffered data to a 
            //receivedString.assign(&(rcvBuf[0]), rcvBuf.size()); // string --> this line is failing.

            // receivingTime = tick_count::now();
            chrono::time_point<std::chrono::system_clock> receivingTime = chrono::system_clock::now();
            // rtt = (receivingTime - sendingTime).seconds() * 1000000.0;
            
            std::string receivedString(buffer);
            
            string queryTag = receivedString.substr(0, receivedString.find(" **"));
            // If the pattern " **" is found that means there is result from server side
            // else there is no result and we don't log the RTT of the query in rttLog
            if (receivedString.find(" **") != string::npos) {
                chrono::duration<double> rtt = receivingTime - sendingTime;
                // Donot print the first two newline character
                rttLog << queryTag.substr(2) << ", " << rtt.count() * 1000000 << endl; // in microseconds
            }
            
            // log the search result from server 
            searchResult << receivedString; 
        }
        else {
            // rttLog << "Server is offline." << endl;
            break;
        }

        i++;
		queryNo++;
        // for testing just send 5 request
        /*if (queryNo == 100) {
          sleep(5);
          break;
        }*/
    }

    // time is up server is not serving anymore, close the socket 
    close(sockfd);
    return 0;
}
