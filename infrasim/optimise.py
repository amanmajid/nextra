'''
    optimise.py
        
        Capacity planning model for Israel, Jordan, and the Palestinian Authority

    @amanmajid
'''

import gurobipy as gp


class model():


    def __init__(self,nodes,edges,flows,**kwargs):
        
        '''
        
        Parameters
        ----------
        nodes : TYPE
            DESCRIPTION.
        edges : TYPE
            DESCRIPTION.
        flows : TYPE
            DESCRIPTION.
        **kwargs : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''



    def build(self):
        '''Build optimisation model using GurobiPy
        '''



    def run(self,pprint=True,write=True):
        '''Function to solve GurobiPy model
        '''



    def debug(self,output_path='../outputs/__cache__/'):
        '''Compute model Irreducible Inconsistent Subsystem (IIS) to help deal with infeasibilies
        '''
        self.model.computeIIS()
        self.model.write(output_path+'debug_report.ilp')