#include "CLucene/StdHeader.h"
#include "CLucene/_clucene-config.h"

#include "CLucene.h"
#include "CLucene/util/Misc.h"
#include "CLucene/store/FSDirectory.h"
#include "CLucene/store/RAMDirectory.h"
#include "CLucene/store/Directory.h"
#include "CLucene/config/repl_tchar.h"
#include "CLucene/config/repl_wchar.h"

//test for memory leaks:
#ifdef _MSC_VER
#ifdef _DEBUG
#define _CRTDBG_MAP_ALLOC
#include <stdlib.h>
#include <crtdbg.h>
#endif
#endif

#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <thread>
#include <sstream>
#include <string.h>
#include <time.h>
#include <unistd.h>
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


void searcher(){
  standard::StandardAnalyzer analyzer;
  //WhitespaceAnalyzer  analyzer;
  //SimpleAnalyzer  analyzer;
  char line[500];
  TCHAR tline[500];
  thread::id myid = this_thread::get_id();
  stringstream ss; ss << myid;
  string log_fn = string("log_") + ss.str() + string(".log");
 
  // TODO: need create a log file per thread. one line per query
  ofstream logfile(log_fn);
  logfile << "open index files " << endl;
  Directory * dir = FSDirectory::getDirectory(indexFileDir);
  IndexReader* reader = IndexReader::open(dir);
  
  

}



int main(int argc, char* argv[])
{
   searcher();   
   return 0;
}
