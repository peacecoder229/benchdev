/*------------------------------------------------------------------------------
* Copyright (C) 2003-2006 Ben van Klinken and the CLucene Team
*
* Distributable under the terms of either the Apache License (Version 2.0) or
* the GNU Lesser General Public License, as specified in the COPYING file.
------------------------------------------------------------------------------*/
#include "CLucene/StdHeader.h"
#include "CLucene/_clucene-config.h"

#include "CLucene.h"
#include "CLucene/util/Misc.h"

#ifdef _MSC_VER
#ifdef _DEBUG
#define _CRTDBG_MAP_ALLOC
#include <stdlib.h>
#include <crtdbg.h>
#endif
#endif
#include <vector>
#include <stdio.h>
#include <iostream>
#include <fstream>
#include <string.h>

using namespace std;
using namespace lucene::util;

void IndexFiles(vector<string>& FileList, const char* target, const bool clearIndex);
void SearchFiles(const char* index);
void getStats(const char* directory);

const char * file_list;
const char * index_location;

int main( int32_t argc, char** argv ){
#ifdef _DEBUG
  _CrtSetDbgFlag ( _CRTDBG_ALLOC_MEM_DF | _CRTDBG_LEAK_CHECK_DF | _CRTDBG_CHECK_ALWAYS_DF | _CRTDBG_CHECK_CRT_DF );
  _crtBreakAlloc=-1;
#endif

  if (argc != 3) {
      printf("Usage: %s index_location file_list\n", argv[0]);
      exit(0);
  }

  index_location = argv[1];
  file_list = argv[2];
  
  uint64_t str = Misc::currentTimeMillis();
  
  ifstream infile(file_list);
  if(infile.fail()) {
    printf("file_list isn't exist, exit now\n");
    return 0;
  }
  vector<string> FileList;
  FileList.clear();
  string line = "";
  while(getline(infile, line)) {
    FileList.push_back(line);
  }
  printf("File number tobe indexed: %d\n", (int)FileList.size());
  
  IndexFiles(FileList, index_location, true);
  getStats(index_location);
  
  
  _lucene_shutdown();
  
  infile.close();
  printf ("\n\nTime taken: %d\n\n", (int32_t)(Misc::currentTimeMillis() - str));
  
  return 0;
}
