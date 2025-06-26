def rearrange_results(listdata, result):
    # Create a dictionary to map names to their results
    result_dict = {res[0]: res for res in result}
    
    # Create last_file list by matching the order of listdata
    last_file = [result_dict[li] for li in listdata if li in result_dict]
    
    return last_file


