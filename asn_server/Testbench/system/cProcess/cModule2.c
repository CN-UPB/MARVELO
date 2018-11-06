#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>

int main(int argc, char *argv[])
{
    int input;
    int output;
    int param;
    int log;
    int optind;
        printf("size inputs = %d\n",argc);
    for (optind = 1; optind < argc; optind++) {
        if (argv[optind][0] == '-'){

        switch (argv[optind][1]) {
        case 'i': input = atoi(argv[optind+1]); break;
        case 'o': output = atoi( argv[optind+1]); break;
        case 'p': param = atoi(argv[optind+1]); break;
        }   
      }
    }   

        printf("input Pipe=%d\n",input);
        printf("output Pipe=%d\n",output);

/******** End Input Arguments ********/

   long length;
   int fh;
   int buffer[10];
   FILE *fp;
   int packetSize;
   packetSize = 1024;
   int floatValue[packetSize];
   int maxpacketNr = 5;


    printf("Openning Pipe\n");

   if ((fp=fdopen(output, "w")) == NULL) {
       perror(" File was not created: ");
       exit(1);
   }
    printf("Writing Pipe\n");
    int pcount;
    int dcount;
    for (pcount = 0; pcount<maxpacketNr ; pcount++){
        for(dcount = 0; dcount<packetSize; dcount++){
            floatValue[dcount] = dcount + pcount*packetSize;
	}
         if(fwrite(floatValue, sizeof(int), packetSize, fp) != packetSize)
    		printf("File write error.");
	}

    printf(" Pipe Wrote\n");
   fclose(fp);

 
   
}   
