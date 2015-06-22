from django.http import Http404, HttpResponse
from django.shortcuts import render
from forms import AnnotationsForm,GraphForm

import os
from math import floor
from collections import defaultdict
import numpy as np
import pandas as pd
import json

import omero
from omeroweb.webclient.decorators import login_required

PATH = '/Users/uqdmatt2/Desktop/temp'

def get_column(path,col):
    num_lines = sum(1 for line in open(path))
    try:
        with open(path) as t_in:
            data = pd.read_csv(t_in,header=1,\
                               sep=r'\t|,',engine='python',\
                               skiprows=range(num_lines-50,num_lines),\
                               index_col=False)

        if type(col) != list:
            return list(data[col].values)
        else:
            vals = []    
            for c in col:
                vals.append(list(data[c].values))
            return vals      
    except:
        print 'there was a problem parsing the data'
        return None
        
def parse_annotation(path):
    num_lines = sum(1 for line in open(path))
    try:
        with open(path) as t_in:
            data = pd.read_csv(t_in,header=1,\
                               sep=r'\t|,',engine='python',\
                               skiprows=range(num_lines-50,num_lines),\
                               index_col=False)  
        columns = []
        for col in data.columns.values:
            columns.append((col,col)) 
        return columns        
    except:
        print 'there was a problem parsing the data'
        return None
        
def download_annotation(ann):
    """
    Downloads the specified file to and returns the path on the server
    
    @param ann:    the file annotation being downloaded
    """ 
    if not os.path.exists(PATH):
        os.makedirs(PATH)
    file_path = os.path.join(PATH, ann.getFile().getName())
    if os.path.isfile(file_path):
        return file_path
    else:
        f = open(str(file_path), 'w')
        print "\nDownloading file to", file_path, "..."
        try:
            for chunk in ann.getFileInChunks():
                f.write(chunk)
        finally:
            f.close()
            print "File downloaded!"
        return file_path

def find_duplicate_annotations(mylist):
    D = defaultdict(list)
    for i,item in enumerate(mylist):
        D[item].append(i)
    return {k:v for k,v in D.items() if len(v)>1}
    
def get_user_annotations(conn,extensions=('txt','csv','xls')):

    params = omero.sys.ParametersI()
    params.exp(conn.getUser().getId())  # only show current user's Datasets
    datasets = conn.getObjects("Dataset", params=params)
    annotations = []
    annotation_names = []
    for dataset in datasets:
        for dsAnn in dataset.listAnnotations():
            if isinstance(dsAnn, omero.gateway.FileAnnotationWrapper):
                annotations.append(dsAnn)
                annotation_names.append(dsAnn.getFile().getName())
        for image in dataset.listChildren():
            for imAnn in image.listAnnotations():
                if isinstance(imAnn, omero.gateway.FileAnnotationWrapper):
                    annotations.append(imAnn)
                    annotation_names.append(imAnn.getFile().getName())
                    
    filtered_anns = []
    filtered_names = []
    for ext in extensions:
        filtered_anns.extend([ann[0] for ann in zip(annotations,annotation_names) if ext in ann[1]])
        filtered_names.extend(["ID:"+str(ann[0].getId())+" "+ann[1] for ann in zip(annotations,annotation_names) if ext in ann[1]])
        
    duplicates = find_duplicate_annotations(filtered_names)
    for k,v in duplicates.iteritems():
        dups = v[1:]
        for d in dups:
            filtered_anns.pop(d)
            filtered_names.pop(d)
        
    return filtered_anns,filtered_names


@login_required()
def index(request, conn=None, **kwargs):
    userFullName = conn.getUser().getFullName()
    anns,names = get_user_annotations(conn)
    form_names = []
    for name in names:
        form_names.append((name,name))
    form = AnnotationsForm(options=form_names)
    context = {'userFullName': userFullName,
               'annotations': anns,
               'annotation_names': names, 
               'form': form}
    return render(request, "omero_graph/index.html", context)
    
@login_required()
def index(request, conn=None, **kwargs):
    userFullName = conn.getUser().getFullName()
    anns,names = get_user_annotations(conn)
    form_names = []
    for name in names:
        form_names.append((name,name))
    if request.POST:
        form = AnnotationsForm(options=form_names,data=request.POST)
        if form.is_valid():
            selected = form.cleaned_data['annotation']
            annId = selected.partition(' ')[0][3:]
            rv = {'selected': selected,
                  'id': annId}
            data = json.dumps(rv)
            return HttpResponse(data, mimetype='application/json')
    else:
        form = AnnotationsForm(options=form_names)
        context = {'userFullName': userFullName,
                   'annotations': anns,
                   'annotation_names': names, 
                   'form': form}
        return render(request, "omero_graph/index.html", context)
            
@login_required()
def plot(request, annotation_id=None, conn=None, **kwargs):
    annotation = conn.getObject("Annotation",annotation_id)
    fpath = download_annotation(annotation)
    cols = parse_annotation(fpath)
    if request.POST and annotation_id:
        print request.POST
        form = GraphForm(options=cols,data=request.POST.copy())
        if form.is_valid():
            title = annotation.getFile().getName()
            x = form.cleaned_data['x']
            y = form.cleaned_data['y']
            xdata = [floor(xd) for xd in get_column(fpath,x)]
            xmin = min(xdata)
            xmax = max(xdata)
            ydata = get_column(fpath,y)
            plot_data = {'title': title, 'x' : x, 'y' : y,\
                         'xdata': xdata, 'ydata': ydata,\
                         'num_series': len(ydata),
                         'xmin': xmin, 'xmax': xmax}
            data = json.dumps(plot_data)
            return HttpResponse(data, mimetype='application/json')
    else:
        form = GraphForm(options=cols)
        #graph_data = {'annotation': annotation,
        #           'columns': cols,'form': form}
        #data = json.dumps(graph_data)
        #return HttpResponse(data, mimetype='application/json')
        
    context = {'annotation': annotation,
               'columns': cols,'setup_form': form}
    return render(request,"omero_graph/plot.html", context)
    