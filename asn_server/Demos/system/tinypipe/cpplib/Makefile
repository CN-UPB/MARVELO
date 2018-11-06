main:
	g++ -lpthread -c -fPIC pipeinterface.cpp -o pipeinterface.o
	g++ -lpthread -shared -Wl,-soname,libpipeinterface.so -o libpipeinterface.so  pipeinterface.o
	
.PHONY: clean

clean:
	rm pipeinterface.o
	rm libpipeinterface.so