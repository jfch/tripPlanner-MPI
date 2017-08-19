#include <iostream>
//#include <conio.h>
#include <iomanip>   
#include "TSPSolver.h"

int main(int argc, char *argv[])
{
	try
	{
		//TSPSolver tsp("we12.txt"); 
		TSPSolver tsp(argv[1]); 

		double time = omp_get_wtime();

		cout << "Parallel: " << endl;
		tsp.solve(false);
		tsp.show();

		cout << omp_get_wtime() - time << "s" << endl << endl;
	    tsp.restart();

		time = omp_get_wtime(); 
		cout << "Sequential: " << endl;
		tsp.solve(true);
		tsp.show();

		cout << omp_get_wtime() - time << "s" << endl;
	}
	catch (exception &e)
	{
		cout << e.what() << endl;
	}
//	cin.get();
	return 0;
}

