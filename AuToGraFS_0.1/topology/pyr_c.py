#!/usr/bin/python
from ase.atom import Atom
from ase.atoms import Atoms
from ase.io import read, write
from ase.lattice.spacegroup import crystal
from ase.calculators.neighborlist import *
from ase.data import *
from math import pi
import numpy as np

def make_pyr_c(names,sizes):

    #work out the expansion factor
    #dist0 = furthest_dummy(mol0)
    #dist1 = furthest_dummy(mol1)

    factor = sum(sizes) #dist0 + dist1

    factor = factor 
    print "Factor =", factor
    a = 2.4495 * factor 
    
    # C -> octahedra, N => midpoints
    pyr_c = crystal(['C', 'N' ], [(0.0, 0.0, 0.0), (0.333333, 0.333333, 0.333333)], spacegroup=206,  #Ia-3
                   cellpar=[a, a, a, 90, 90, 90])
    
    
    #write('test.xyz',pyr_c)
    
    eps = 0.1
    model_molecule={}
    n_obj = -1 #initialise to -1 such that it can be indexed at start of add
    n_tags = 0
    
    #First detect global bonding
    cov_rad=[]
    for atom in pyr_c:
        #cov_rad.append(covalent_radii[atom.number])
        cov_rad.append(factor / 2)
    
    #print cov_rad
    
    nlist = NeighborList(cov_rad,skin=0.01,self_interaction=False,bothways=True)
    nlist.build(pyr_c)
    
    #To sort out tags, we need to label each bond
    nbond = 1
    bond_matrix = np.zeros( (len(pyr_c),len(pyr_c)) )
    pbc_bond_matrix = np.zeros( (len(pyr_c),len(pyr_c)) )
    
    bond_dict = {}
    
    for atom in pyr_c:
        print "---------------------"
        indices, offsets = nlist.get_neighbors(atom.index)
        for index,offset in zip(indices,offsets):
            print atom.index, index, atom.symbol, pyr_c[index].symbol, offset, pyr_c.get_distance(atom.index,index,mic=True)
            if atom.index < index:
                this_bond = [atom.index, index]
                for o in offset:
                    this_bond.append(o)
                bond = tuple(this_bond)
                print bond
                bond_dict[bond] = nbond
                #Now we need to find the same bond the other direction to get the offsets right
                indices2,offsets2 = nlist.get_neighbors(index)
                for i2,o2 in zip(indices2,offsets2):
                    if i2 == atom.index:
                        #print "sum of offsets = ", offset, o2, sum(offset + o2)
                        if sum(offset + o2) == 0: #same bond
                            this_bond = [index, atom.index]
                            for o in o2:
                                this_bond.append(o)
                            bond = tuple(this_bond)
                            #print bond
                            bond_dict[bond] = nbond
                nbond +=1
    
    print nbond
    for k,v in bond_dict.items():
        print k,v
    
    #Start with C (octahedra) 
    for atom in pyr_c:
        if atom.symbol == 'C':
            print'======================================='
            print 'C Atom ',atom.index
            n_obj+=1
            model_molecule[n_obj] = Atoms()
            model_molecule[n_obj] += atom
            model_molecule[n_obj][0].original_index = atom.index
            model_molecule[n_obj][0].symbol = 'F' 
            indices, offsets = nlist.get_neighbors(atom.index)
            #Just checking the symbols here
            print indices
            print offsets
            symbols = ([pyr_c[index].symbol for index in indices])
            symbol_string = ''.join(sorted([pyr_c[index].symbol for index in indices]))
            #print symbol_string
            #for i,o in zip(indices, offsets):
            #    print i,o
            for index,offset in zip(indices,offsets):
                print atom.index, index, offset
                this_bond = [atom.index, index]
                for o in offset:
                    this_bond.append(o)
                bond = tuple(this_bond)
                #print bond_dict[bond]
                if pyr_c[index].symbol == 'N' and abs(pyr_c.get_distance(atom.index,index,mic=True) - factor) < eps:
                    if any(o != 0 for o in offset):
                        #If we're going over a periodic boundary, we need to negate the tag
                        model_molecule[n_obj] += pyr_c[index]
                        model_molecule[n_obj].positions[-1] = pyr_c.positions[index] + np.dot(offset, pyr_c.get_cell())
                        model_molecule[n_obj][-1].tag = -bond_dict[bond]
                    else:
                        model_molecule[n_obj] += pyr_c[index]
                        model_molecule[n_obj][-1].tag = bond_dict[bond] 
                        model_molecule[n_obj].positions[-1] = pyr_c.positions[index] + np.dot(offset, pyr_c.get_cell())
    
    n_centers = n_obj
    #
    #
    ##Now we do the  N  (triangles)
    for atom in pyr_c:
        if atom.symbol == 'N':
            #print'======================================='
            #print 'N Atom ',atom.index, " finding edges"
            n_obj+=1
            model_molecule[n_obj] = Atoms()
            model_molecule[n_obj] += atom
            indices, offsets = nlist.get_neighbors(atom.index)
            for index,offset in zip(indices,offsets):
                print index, offset, pyr_c[index].symbol
                this_bond = [atom.index, index]
                for o in offset:
                    this_bond.append(o)
                bond = tuple(this_bond)
                #if not bond_dict.has_key(bond):
                    #Then 
                if pyr_c[index].symbol == 'C' and abs(pyr_c.get_distance(atom.index,index,mic=True) - factor) < eps: #necessary check, because some atoms are closer than unit distance
                    if any(o != 0 for o in offset):
                        #If we're going over a periodic boundary, we need to negate the tag
                        model_molecule[n_obj] += pyr_c[index]
                        model_molecule[n_obj].positions[-1] = pyr_c.positions[index] + np.dot(offset, pyr_c.get_cell())
                        model_molecule[n_obj][-1].tag = -bond_dict[bond]
                    else:
                        model_molecule[n_obj] += pyr_c[index]
                        model_molecule[n_obj][-1].tag = bond_dict[bond] 
                        model_molecule[n_obj].positions[-1] = pyr_c.positions[index] + np.dot(offset, pyr_c.get_cell())
    
    
    #
    #
    #
    f = open('pyr_c.model','w')
    g = open('control-mofgen.txt','w')
    #Just for checking, now lets gather everything in the model_molecule dict into one big thing and print it
    #test_mol = Atoms()
    #for obj in model_molecule:
    #    test_mol += model_molecule[obj]
    
    #write('test_model.xyz',test_mol)
    
    #print n_centers, n_model, n_obj
    #Headers and cell
    f.write('%-20s %-3d\n' %('Number of objects =',n_obj+1))
    f.write('%-20s\n' %('build = systre'))
    f.write('%5s\n' %('Cell:'))
    f.write('%8.3f %8.3f %8.3f \n' %
              (pyr_c.get_cell()[0][0],
               pyr_c.get_cell()[0][1],
               pyr_c.get_cell()[0][2]))
    f.write('%8.3f %8.3f %8.3f \n' %
              (pyr_c.get_cell()[1][0],
               pyr_c.get_cell()[1][1],
               pyr_c.get_cell()[1][2]))
    f.write('%8.3f %8.3f %8.3f \n' %
              (pyr_c.get_cell()[2][0],
               pyr_c.get_cell()[2][1],
               pyr_c.get_cell()[2][2])) 
    
    g.write('%-20s\n' %('model = pyr_c'))

    #Now write stuff          
    for obj in xrange(n_centers+1):
        f.write('\n%-8s %-3d\n' %('Center: ', obj+1))
        f.write('%-3d\n' %(len(model_molecule[obj])))
        f.write('%-20s\n' %('type = octahedral_2'))
        #process positions to make it a bit more ideal
        for atom in model_molecule[obj]:
            #if atom.symbol == 'C':
            if atom.index != 0:
                model_molecule[obj].set_distance(atom.index,0,1.0,fix=1)
        for atom in model_molecule[obj]:
            (x,y,z) = atom.position
            #print atom.symbol, atom.position, atom.tag
            if atom.tag:
                f.write('%-2s %15.8f %15.8f %15.8f %-4s\n' % ('X', x, y, z, atom.tag))
                #f.write('%-2s %15.8f %15.8f %15.8f %-4s\n' % (atom.symbol, x, y, z, atom.tag))
            else:
                f.write('%-2s %15.8f %15.8f %15.8f\n' % ('Q', x, y, z))
                #f.write('%-2s %15.8f %15.8f %15.8f\n' % (atom.symbol, x, y, z))
        g.write('%-9s %-50s\n' %('center =', names[0]))
    
    for obj in xrange(n_centers+1,n_obj+1):
        f.write('\n%-8s %-3d\n' %('Linker: ', obj-n_centers))
        f.write('%-3d\n' %(len(model_molecule[obj])))
        f.write('%-20s\n' %('type = triangle'))
        #process positions to make it a bit more ideal
        for atom in model_molecule[obj]:
            #if atom.symbol == 'C': 
            if atom.index != 0:
                model_molecule[obj].set_distance(atom.index,0,1.0,fix=1)
        for atom in model_molecule[obj]:
            (x,y,z) = atom.position
            #print atom.symbol, atom.position, atom.tag
            if atom.tag:
                f.write('%-2s %15.8f %15.8f %15.8f %-4s\n' % ('X', x, y, z, atom.tag))
                #f.write('%-2s %15.8f %15.8f %15.8f %-4s\n' % (atom.symbol, x, y, z, atom.tag))
            else:
                f.write('%-2s %15.8f %15.8f %15.8f\n' % ('Q', x, y, z))
                #f.write('%-2s %15.8f %15.8f %15.8f\n' % (atom.symbol, x, y, z))
        g.write('%-9s %-50s\n' %('linker =', names[1]))
    
    #
    #
    #test_mol = Atoms()
    #for obj in model_molecule:
    #    test_mol += model_molecule[obj]
    #
    #write('test_model2.xyz',test_mol)
