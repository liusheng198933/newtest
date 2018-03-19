#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main()
{

  FILE *filep;

  char filepath[100];
  time_t t;
  srand((unsigned) time(&t));
  int x;
  x = rand() % 200;

  sprintf(filepath, "/home/shengliu/Workspace/mininet/haha/API/time/debug_%d.txt", x);
  puts(filepath);
  filep = fopen(filepath, "aw+");

  fprintf(filep, "haha\n");
  fclose(filep);
  return 0;
}
