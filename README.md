# Balance Projector

Shows your future account balances according to a [spec file](balance-projector.dist.yml).

<img src="https://github.com/crucialwebstudio/balance-projector/blob/main/screenshot.png?raw=true" alt="Balance Projector" style="max-width: 100%"/>

## Getting Started

1. Clone the project.
   ```shell
   $ git clone git@github.com:crucialwebstudio/balance-projector.git
   $ cd ./balance-projector
   ```
2. Initialize a vritual environment.
   ```shell
   $ make init
   $ source venv/bin/activate
   ```

3. Start the dashboard.
   ```shell
   (venv) projector dash
   ```
   
   The dashboard will be accessible in your browser at http://127.0.0.1:8050/

## Running tests

Run the tests.
```shell
(venv) nose2
```