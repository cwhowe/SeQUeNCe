import logging
import multiprocessing
import papermill as pm

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_script(iteration):
    notebook_path = 'example/Multi_Node_Framework_CSV.ipynb'
    output_path = f'example/outputs/Multi_Node_Framework_WORKING_output_{iteration}.ipynb'

    try:
        logging.info(f"Starting execution of notebook for iteration {iteration}")
        pm.execute_notebook(
            notebook_path,
            output_path,
            parameters={'run_cycle': iteration}
        )
        logging.info(f"Completed execution of notebook for iteration {iteration}")
    except Exception as e:
        logging.error(f"Error executing notebook for iteration {iteration}: {e}")

if __name__ == "__main__":
    setup_logging()
    processes = []

    for i in range(4):
        p = multiprocessing.Process(target=run_script, args=(i,))
        p.start()
        processes.append(p)
        logging.info(f"Process for iteration {i} started")

    for p in processes:
        p.join()
        logging.info("Process joined")
