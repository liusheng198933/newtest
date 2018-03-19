#include <sys/time.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

int main()
{
  struct timeval tval_cur;
  FILE *filep;

  gettimeofday(&tval_cur, NULL);

  // Some code you want to time, for example:
  //sleep(1);

  //gettimeofday(&tval_after, NULL);

  //timersub(&tval_after, &tval_before, &tval_result);

  filep = fopen("/home/shengliu/Workspace/mininet/haha/API/time/debug.txt", "aw+");
  fprintf(filep, "begin time %ld %ld\n", (long int)tval_cur.tv_sec, (long int)tval_cur.tv_usec);
  fclose(filep);

  //printf("Time now: %ld, %ld\n", (long int)tval_cur.tv_sec, (long int)tval_cur.tv_usec);

  //printf("Time now: %ld.%06ld\n", (long int)tval_after.tv_sec, (long int)tval_after.tv_usec);

  //printf("Time elapsed: %ld.%06ld\n", (long int)tval_result.tv_sec, (long int)tval_result.tv_usec);
}
