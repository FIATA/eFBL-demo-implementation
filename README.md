# eFBL test implementation

This is an implementation of the eFBL standard for FIATA. It is a test implementation and should not be used in
production.
It has been developed using python for clarity and simplicity.


## Installation

### Prerequisites

Before you start, ensure you have Poetry installed on your system. You can install Poetry by following the
instructions [here](https://python-poetry.org/docs/#installation).

### Installation Steps

1. Clone the repository:

    ```bash
    git clone https://github.com/FIATA/eFBL-demo-implementation.git
    ```

2. Navigate to the project directory:

    ```bash
    cd eFBL-demo-implementation
    ```

3. Install project dependencies using Poetry:

    ```bash
    poetry install
    ```

4. Fill in the `.env` file with the required environment variables. You can use the `.env.example` file as a template.


## Usage

Check the code in efbl library to see how to use it. The usage_example.py script is a good starting point.


### Running an Example Script

To run the `usage_example.py` script within the Poetry environment, follow these steps:

1. Activate the Poetry environment:

    ```bash
    poetry shell
    ```

2. Run the script:

    ```bash
    python usage_example.py
    ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- **Gregory Favre**: greg@beyondthewall.ch
