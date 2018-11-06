#include <stdbool.h>
#include <stdio.h>
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
        case 'i': input = (int) argv[optind][3]/7; break;
        case 'o': output = (int) argv[optind][3]/7; break;
        case 'p': param = argv[optind][3]; break;
        }   
      }
    }   

        printf("Openning Pipe=%d\n",input);
        printf("Openning Pipe=%d\n",output);

/******** End Input Arguments ********/

   long length;
   int fh;
   int buffer[10];
   FILE *fp;
   int floatValue[5] = { 1, 2, 3, 4, 5 };
   char outputPipe[] = "3";


    printf("Openning Pipe\n");

   if ((fp=fopen(outputPipe, "w")) == NULL) {
       perror(" File was not created: ");
       exit(1);
   }
    printf("Writing Pipe\n");

  if(fwrite(floatValue, sizeof(int), 5, fp) != 5)
    printf("File write error.");

   fclose(fp);
    printf(" Pipe Wrote\n");
 
   if (-1 == (fh = open(outputPipe, O_RDWR|O_APPEND))) {
      perror("Unable to open sample.dat");
      exit(1);
   }

   if (NULL == (fp = fdopen(fh, "r"))) {
      perror("fdopen failed");
      close(fh);
      exit(1);
   }
   if(fread(buffer, sizeof(int), 5, fp) != 5) {
    if(feof(fp))
       printf("Premature end of file.");
    else
       printf("File read error.");
  }
   printf("Successfully read from the stream the following:\n");
     int jj; 
    for( jj = 0; jj<10 ;jj++)
     printf("%d \n",buffer[jj]);

   fclose(fp);
   return 1;
 
   /****************************************************************
    * The output should be:
    *
    * Creating sample.dat.
    * Successfully read from the stream the following:
    * Sample Program.*/
}   
