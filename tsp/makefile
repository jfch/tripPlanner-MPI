exe = tsp
SO = tsp.so
%.o: %.cpp
	g++ -c -fopenmp -lgomp -fPIC $<
objects = main.o GenPermutation.o Matrix.o TSPSolver.o 
$(exe) : $(objects)
	g++ -lgomp $(objects) -o $(exe)
$(SO) : $(objects)
	g++ -shared -lgomp $(objects) -o $(SO)
main.o : TSPSolver.h
GenPermutation.o : GenPermutation.h
Matrix.o : Matrix.h
TSPSolver.o : TSPSolver.h
.PHONY : clean
clean :
	rm $(exe) $(objects)
