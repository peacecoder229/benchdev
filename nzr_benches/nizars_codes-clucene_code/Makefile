.ONESHELL:
FLAGS=-g -std=c++11 -O3

LIB_FILE_IO=build_file_io
LIB_MMAP=build_mmap
BUILD_THREADS_NUM=20

all:
	cd ../../../
	ls
	cp -f CMakeLists_file_io.txt  CMakeLists.txt
	mkdir ${LIB_FILE_IO} 2 >& /dev/null
	cd ${LIB_FILE_IO}
	cmake ..
	make -j${BUILD_THREADS_NUM}
	cd ..
	cp -f CMakeLists_mmap.txt  CMakeLists.txt
	mkdir ${LIB_MMAP} 2 >& /dev/null
	cd ${LIB_MMAP}
	cmake ..
	make -j${BUILD_THREADS_NUM}
	pwd
	cd ../src/benchmark-dev/
	cp ../../${LIB_FILE_IO}/bin/libclucene-core-static.a libclucene-core-static-file-io.a
	cp ../../${LIB_FILE_IO}/bin/libclucene-shared-static.a libclucene-shared-static-file-io.a
	mkdir -p include/CLucene
	cp ../core/*.h include
	cp -r ../core/CLucene/* ../shared/CLucene/* ../../${LIB_MMAP}/src/shared/CLucene/*  include/CLucene
	cp ../../${LIB_MMAP}/bin/libclucene-core.so.1 .
	unlink libclucene-core.so
	unlink libclucene-shared.so
	ln -s libclucene-core.so.1 libclucene-core.so
	cp ../../${LIB_MMAP}/bin/libclucene-shared.so.1 .
	ln -s libclucene-shared.so.1 libclucene-shared.so
	g++ ${FLAGS} -o clucene_search_main/main_indexer clucene_search_main/MainIndexer.cpp clucene_search_main/Statistics.cpp clucene_search_main/IndexFiles.cpp -I./include  -L./ -lclucene-core-static-file-io -lclucene-shared-static-file-io -lpthread -lz
	
	g++ ${FLAGS}  -o clucene_search_main/server clucene_search_main/Server.cpp clucene_search_main/SearchFiles.cpp  clucene_search_main/Statistics.cpp -I./include  -L./ -lclucene-core -lclucene-shared -ltbb -lpthread
	
	g++ ${FLAGS}  -o clucene_search_main/serverSingleThread clucene_search_main/ServerSingleThread.cpp clucene_search_main/SearchFiles.cpp  clucene_search_main/Statistics.cpp -I./include  -L./ -lclucene-core -lclucene-shared -ltbb -lpthread
	
	g++ ${FLAGS} -o clucene_search_main/serverMultiThread clucene_search_main/ServerMultiThread.cpp clucene_search_main/SearchFiles.cpp  clucene_search_main/Statistics.cpp -I./include  -L./ -lclucene-core -lclucene-shared -ltbb -lpthread
    
	g++ ${FLAGS}  -o clucene_search_main/client clucene_search_main/Client.cpp

clean:
	rm -rf include
	rm -f libclucene-core*.* libclucene-shared*.*
	rm -f main_indexer main_searcher
	rm -rf ../../${LIB_FILE_IO} ../../${LIB_MMAP}

