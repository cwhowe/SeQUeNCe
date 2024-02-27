import multiprocessing
import papermill as pm

def run_script(iteration):
    notebook_path = 'example/Multi_Node_Framework_WORKING.ipynb'
    output_path = f'example/outputs/Multi_Node_Framework_WORKING_output_{iteration}.ipynb'

    pm.execute_notebook(
        notebook_path,
        output_path,
        parameters={'run_cycle': iteration}
    )

if __name__ == "__main__":
    processes = []

    for i in range(16):
        #print(f"Creating process for iteration {i}")
        p = multiprocessing.Process(target=run_script, args=(i,))
        p.start()
        processes.append(p)
        #print(f"Process for iteration {i} started")

    for process in processes:
        process.join()
        #print("Process joined")
