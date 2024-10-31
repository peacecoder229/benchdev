/*------------------------------------------------------------------------------
* Copyright (C) 2003-2006 Ben van Klinken and the CLucene Team
*
* Distributable under the terms of either the Apache License (Version 2.0) or
* the GNU Lesser General Public License, as specified in the COPYING file.
------------------------------------------------------------------------------*/

#include <stdio.h>
#include <iostream>
#include <fstream>
#include <sys/stat.h>
#include <cctype>
#include <string.h>
#include <algorithm>

#include "CLucene/StdHeader.h"
#include "CLucene/_clucene-config.h"

#include "CLucene.h"
#include "CLucene/util/CLStreams.h"
#include "CLucene/util/dirent.h"
#include "CLucene/config/repl_tchar.h"
#include "CLucene/util/Misc.h"
#include "CLucene/util/StringBuffer.h"

using namespace std;
using namespace lucene::index;
using namespace lucene::analysis;
using namespace lucene::util;
using namespace lucene::store;
using namespace lucene::document;

void FileDocument(const char* path, IndexWriter* writer){
	TCHAR t_path[CL_MAX_DIR];
	STRCPY_AtoT(t_path, path, CL_MAX_DIR);
	
	char pre[100] = "";
	char* filepath = strcat(pre, path);
	size_t line_size = 1024;

	//printf("Filepath: %s\n", filepath);
	
	struct stat t_stat;
	time_t time;
	char time_buf[200];
	struct tm *tm;
	if(stat(filepath, &t_stat) != 0) {
		printf("File does not exist\n");
	} else {
		time = t_stat.st_mtime;
		//tm = localtime(&time);
		//strftime(time_buf, sizeof(time_buf), "%d.%m.%Y %H:%M:%S", tm);
		//printf("Date modified: %s\n", time_buf);
	}
	
	FILE* fh = fopen(filepath, "r");
	if (fh) {
		Document doc;

		size_t read;
		char buf[line_size];
		
		char* search;
		char* first;
		char* second;
		char abuf[line_size];
		TCHAR tbuf[line_size];
		StringBuffer contents, url, title;
		size_t len;
		char tb1 [line_size];
		char tb2 [line_size];
				
		// read first line, should have url and title
		if (fgets(buf, line_size, fh)) {

			// look for url (format dependant -> "url=\...\" is what we're looking for)
			if ((search = strstr(buf, "url=\""))) {
				if ((first = strchr(search, '\"')) && (second = strchr(first+1, '\"'))) {
					// get length of url
					len = second-(first+1);
					
					// transform url string buffer into TCHAR buffer and append to our url StringBuffer
					// make sure to null terminate both buffers to ensure no overlap
					strncpy(abuf, first+1, len);
					abuf[len] = 0;
					//printf("URL: %s\n", abuf);
					STRCPY_AtoT(tbuf,abuf,len);
				        tbuf[len] = 0;
					url.append(tbuf);

					// create field "url" that is not tokenized
					//doc.add( *_CLNEW Field(_T("url"), url.getBuffer(), Field::STORE_NO | Field::INDEX_UNTOKENIZED) );
				}
			}
			
			// look for title (format depedant -> "title=\...\" is what we're looking for)
			if ((search = strstr(buf, "title=\""))) {
				if ((first = strchr(search, '\"')) && (second = strchr(first+1, '\"'))) {
					// get length of title
					len = second-(first+1);

					// transform url string buffer into TCHAR buffer and append to our url StringBuffer
					// make sure to null terminate both buffers to ensure no overlap
					strncpy(abuf, first+1, len);
					abuf[len] = 0;
					//printf("Title: %s\n", abuf);
					STRCPY_AtoT(tbuf,abuf,len);
				        tbuf[len] = 0;
					title.append(tbuf);

					// create field "title" that is tokenized
					doc.add( *_CLNEW Field(_T("title"), title.getBuffer(), Field::STORE_YES | Field::INDEX_TOKENIZED) );					     	   
				 } 
			}
			
			// now continue reading file until end
			while(fgets(buf, line_size, fh)){
				
				//see if we are at a new document in file
				if ((search = strstr(buf, "</doc>"))) {
					
					// first add the contents we've been collecting to previous doc, and path
					doc.add( *_CLNEW Field(_T("contents"), contents.getBuffer(), Field::STORE_COMPRESS | Field::INDEX_TOKENIZED) );
					doc.add( *_CLNEW Field(_T("path"), t_path, Field::STORE_YES | Field::INDEX_UNTOKENIZED) );
					doc.add( *_CLNEW Field(_T("modified"), DateTools::timeToString(time), Field::STORE_NO | Field::INDEX_UNTOKENIZED));
	

					/* print out fields
					len = _tcslen(doc.getField(_T("url"))->stringValue());
					STRCPY_TtoA(tb1, doc.getField(_T("url"))->stringValue(), len);
					tb1[len] = 0;
					len = _tcslen(doc.getField(_T("title"))->stringValue());
					STRCPY_TtoA(tb2, doc.getField(_T("title"))->stringValue(), len);
					tb2[len] = 0;
					//printf("URL: %s\nTitle: %s\n", tb1, tb2);
					len = _tcslen(doc.getField(_T("modified"))->stringValue());
					STRCPY_TtoA(tb1, doc.getField(_T("modified"))->stringValue(), len);
					tb1[len] = 0;
					printf("Date modified: %s\n", tb1);
					*/
		
					/* generate the phrase_query_file, leave commented if file exists
					ofstream phraseQueryFile;
					phraseQueryFile.open("phrase_query_file", ios_base::app);
					phraseQueryFile.write(strcat(tb2,"\n"), len+1);
					phraseQueryFile.close();
					*/
						
					/* print out contents field
					len = _tcslen(doc.getField(_T("contents"))->stringValue());
					char tb3[len];
					STRCPY_TtoA(tb3, doc.getField(_T("contents"))->stringValue(), len);
					tb3[len] = 0;
					//printf("Contents:\n%s\n", tb3);
					*/
	
					// add document to index writer and clear it and buffers for reuse
					writer->addDocument(&doc);
					doc.clear();
					title.clear();
					url.clear();
					contents.clear();
	

					// now look for next title and url and add them
					if (fgets(buf, line_size, fh)) {

						// look for url (format dependant -> "url=\...\" is what we're looking for)
						if ((search = strstr(buf, "url=\""))) {
							if ((first = strchr(search, '\"')) && (second = strchr(first+1, '\"'))) {
								// get length of url
								len = second-(first+1);
								
								// transform url string buffer into TCHAR buffer and append to our url StringBuffer
								// make sure to null terminate both buffers to ensure no overlap
								strncpy(abuf, first+1, len);
								abuf[len] = 0;
								//printf("URL: %s\n", abuf);
								STRCPY_AtoT(tbuf,abuf,len);
								tbuf[len] = 0;
								url.append(tbuf);

								// create field "url" that is not tokenized
								//doc.add( *_CLNEW Field(_T("url"), url.getBuffer(), Field::STORE_NO | Field::INDEX_NO) );
							}
						}
						
						// look for title (format depedant -> "title=\...\" is what we're looking for)
						if ((search = strstr(buf, "title=\""))) {
							if ((first = strchr(search, '\"')) && (second = strchr(first+1, '\"'))) {
								// get length of title
								len = second-(first+1);

								// transform url string buffer into TCHAR buffer and append to our url StringBuffer
								// make sure to null terminate both buffers to ensure no overlap
								strncpy(abuf, first+1, len);
								abuf[len] = 0;
								//printf("Title: %s\n", abuf);
								STRCPY_AtoT(tbuf,abuf,len);
								tbuf[len] = 0;
								title.append(tbuf);

								// create field "title" that is tokenized
								doc.add( *_CLNEW Field(_T("title"), title.getBuffer(), Field::STORE_YES | Field::INDEX_TOKENIZED) );					     	    } 
						}	
					}					
				} else {	
					// if still in current document, add line to contents and keep going
					STRCPY_AtoT(tbuf,buf,line_size);
					contents.append(tbuf);
				}
			}

			fclose(fh);

		}
	} else {
		printf("File %s does not exist\n", filepath);
	}
}


void indexDocs(IndexWriter* writer, vector<string>& files) {

  vector<string>::iterator itr = files.begin();

  int i=0;
  while ( itr != files.end() ){
    const char* path = itr->c_str();
    printf( "adding file %d from filelist: %s\n", ++i, path );
    FileDocument( path, writer );
    ++itr;
  }
}


void indexDocs(IndexWriter* writer, const char* directory) {
    vector<string> files;
    std::sort(files.begin(),files.end());
    Misc::listFiles(directory,files,true);
    vector<string>::iterator itr = files.begin();

    // Re-use the document object
    int i=0;
    while ( itr != files.end() ){
        const char* path = itr->c_str();
        printf( "adding file %d: %s\n", ++i, path );
        FileDocument( path, writer );
        ++itr;
    }
}


void IndexFiles(vector<string>& FileList, const char* target, const bool clearIndex){
	IndexWriter* writer = NULL;
	//lucene::analysis::WhitespaceAnalyzer an;    // Note: whitespaceanalyzer doesn't do as expected
	lucene::analysis::standard::StandardAnalyzer an;
	//lucene::analysis::SimpleAnalyzer an;
	//lucene::analysis::StopAnalyzer an;

	if ( !clearIndex && IndexReader::indexExists(target) ){
		if ( IndexReader::isLocked(target) ){
			printf("Index was locked... unlocking it.\n");
			IndexReader::unlock(target);
    }
		writer = _CLNEW IndexWriter( target, &an, false);
	}else{
		writer = _CLNEW IndexWriter( target ,&an, true);
	}

  //writer->setInfoStream(&std::cout);

  // We can tell the writer to flush at certain occasions
  //writer->setRAMBufferSizeMB(0.5);
  //writer->setMaxBufferedDocs(3);

  // To bypass a possible exception (we have no idea what we will be indexing...)
  writer->setMaxFieldLength(0x7FFFFFFFL); // LUCENE_INT32_MAX_SHOULDBE

  // Turn this off to make indexing faster; we'll turn it on later before optimizing
  writer->setUseCompoundFile(false);

	uint64_t str = Misc::currentTimeMillis();

	indexDocs(writer, FileList);

  // Make the index use as little files as possible, and optimize it
  writer->setUseCompoundFile(true);
  writer->optimize();

  // Close and clean up
  writer->close();
	_CLLDELETE(writer);

	printf("Indexing took: %d ms.\n\n", (int32_t)(Misc::currentTimeMillis() - str));
}


void IndexFiles(const char* path, const char* target, const bool clearIndex){
	IndexWriter* writer = NULL;
	lucene::analysis::WhitespaceAnalyzer an;

	if ( !clearIndex && IndexReader::indexExists(target) ){
		if ( IndexReader::isLocked(target) ){
			printf("Index was locked... unlocking it.\n");
			IndexReader::unlock(target);
		}
    
		writer = _CLNEW IndexWriter( target, &an, false);
	}else{
		writer = _CLNEW IndexWriter( target ,&an, true);
	}
  
  //writer->setInfoStream(&std::cout);
  
  // We can tell the writer to flush at certain occasions
  //writer->setRAMBufferSizeMB(0.5);
  //writer->setMaxBufferedDocs(3);
  
  // To bypass a possible exception (we have no idea what we will be indexing...)
  writer->setMaxFieldLength(0x7FFFFFFFL); // LUCENE_INT32_MAX_SHOULDBE
  
  // Turn this off to make indexing faster; we'll turn it on later before optimizing
  writer->setUseCompoundFile(false);
  
  uint64_t str = Misc::currentTimeMillis();
    
  indexDocs(writer, path);
  
  // Make the index use as little files as possible, and optimize it
  writer->setUseCompoundFile(true);
  writer->optimize();
  // Close and clean up
  writer->close();
  _CLLDELETE(writer);
  
  printf("Indexing took: %d ms.\n\n", (int32_t)(Misc::currentTimeMillis() - str));
}
