'''
    optimise.py
        
        Capacity planning model for Israel, Jordan, and the Palestinian Authority

    @amanmajid
'''

import gurobipy as gp


class model():


    def __init__(self,path_to_nodes,path_to_edges,path_to_flows,**kwargs):
        
        '''
        
        Parameters
        ----------
        path_to_nodes : str
            DESCRIPTION.
        path_to_edges : str
            DESCRIPTION.
        path_to_flows : str
            DESCRIPTION.
        **kwargs : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
    
        # read data
        self.nodes = read_node_data(path_to_nodes)
        self.edges = read_edge_data(path_to_edges)
        self.flows = read_flow_data(path_to_flows)


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