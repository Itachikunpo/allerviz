# <img src="static/images/allerviz_logo.svg" width="70"/> AllerViz


## Overview

What we are trying to accomplish is to create a more user-friendly, easy, convenient and reliable experience when searching for restaurant recommendations for people with common food allergies or preferences of certain ingredients. Visually, we would like to list/show users restaurants that are evaluated to have the best probability of menu item choices that are allergen free/friendly.


## Setup Environment/Dependencies

***These instructions are only verified for \*nix type systems!***

* `conda == 4.9.2`
    * Install conda from either [Anaconda](https://www.anaconda.com/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) and create the environment with the `environment.yml`

        ```bash
        conda env create -f environment.yml
        ```

## Getting Started

1. Activate conda environment:

    ```bash
    conda activate allerviz
    ```

2. In a separate terminal session, in the *allerviz* conda environment, start the MongoDB service:

    ```bash
    mongod --dbpath database/mongo
    ```

3. Flask app startup, in the *allervix* conda environment:

    ```bash
    python run.py
    ```

3. Navigate to http://127.0.0.1:3001/ for the application.
