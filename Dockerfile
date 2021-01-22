FROM jupyter/base-notebook:latest

USER root

RUN pip install zeep beautifulsoup4 zeep urllib3 requests \
    && pip install -U pip

USER $NB_UID

COPY jupyter_notebook_config.json .jupyter/
COPY ["Lab guide.pdf", "AXL.pdf", "*.ipynb", "/home/jovyan/"]

# COPY connection_parameters.py /home/jovyan/work/

EXPOSE 8888

