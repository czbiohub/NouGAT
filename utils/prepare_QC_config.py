import sys, os, yaml, glob
import subprocess
import argparse



def main(args):
    workingDir = os.getcwd()
    samples_data_dir = args.sample_data_dir
    for sample_dir_name in [dir for dir in os.listdir(samples_data_dir) if os.path.isdir(os.path.join(samples_data_dir, dir))]:
        SampleQC_folder = os.path.join(os.getcwd(), sample_dir_name)
        if not os.path.exists(SampleQC_folder):
            os.makedirs(SampleQC_folder)
        else:
            print "done ({} folder already present, assumed already run)".format(SampleQC_folder)
        os.chdir(SampleQC_folder)
    
        sample_YAML_name = os.path.join(SampleQC_folder, "{}_QC.yaml".format(sample_dir_name))
        sample_YAML = open(sample_YAML_name, 'w')
       
        sample_YAML.write("operation:\n")
        sample_YAML.write(" QCcontrol:\n")
        sample_YAML.write("  tool: abyss\n")
        sample_YAML.write("genomeSize: {}\n".format(args.genomeSize))
        sample_YAML.write("kmer: {}\n".format(args.kmer))
        sample_YAML.write("libraries:\n")
        
        sample_data_dir = os.path.join(samples_data_dir,sample_dir_name)
        sample_files = [ f for f in os.listdir(sample_data_dir) if os.path.isfile(os.path.join(sample_data_dir,f))]

        pair1_file = ""
        pair2_file = ""
        single     = ""
        sample_YAML.write(" lib1:\n")
        for file in sample_files:
            if "_R1_" in file or "_1.fastq.gz" in file:
                if pair1_file:
                    sys.exit("Error: processing sample {} found more that one library/run for read 1".format(sample_dir_name))
                pair1_file = os.path.join(sample_data_dir,file)
                sample_YAML.write("  pair1: {}\n".format(pair1_file))
            elif "_R2_" in file or "_2.fastq.gz" in file:
                if pair2_file:
                    sys.exit("Error: processing sample {} found more that one library/run for read 2".format(sample_dir_name))
                pair2_file = os.path.join(sample_data_dir,file)
                sample_YAML.write("  pair2: {}\n".format(pair2_file))
            elif "merged" in file or "single" in file:
                single = os.path.join(sample_data_dir,file)

        sample_YAML.write("  orientation: {}\n".format(args.orientation))
        sample_YAML.write("  insert: {}\n".format(args.insert))
        sample_YAML.write("  std: {}\n".format(args.std))
        if single != "":
            sample_YAML.write(" lib2:\n")
            sample_YAML.write("  pair1: {}\n".format(single))
            sample_YAML.write("  pair2:\n")
            sample_YAML.write("  orientation: none\n")
            sample_YAML.write("  insert: 0\n")
            sample_YAML.write("  std: 0\n")

        sample_YAML.close
        if(args.global_config is not None):
            submit_job(sample_YAML_name, args.global_config, sample_dir_name)

        os.chdir(workingDir)


def submit_job(sample_config, global_config, sample_name):
    workingDir = os.getcwd()
    slurm_file = os.path.join(workingDir, "{}.slurm".format(sample_name))
    slurm_handle = open(slurm_file, "w")

    slurm_handle.write("#! /bin/bash -l\n")
    slurm_handle.write("set -e\n")
    slurm_handle.write("#SBATCH -A a2010002\n")
    slurm_handle.write("#SBATCH -o {}_QC.out\n".format(sample_name))
    slurm_handle.write("#SBATCH -e {}_QC.err\n".format(sample_name))
    slurm_handle.write("#SBATCH -J {}_QC.job\n".format(sample_name))
    slurm_handle.write("#SBATCH -p node -n 8\n")
    slurm_handle.write("#SBATCH -t 05:00:00\n")
    slurm_handle.write("#SBATCH --mail-user francesco.vezzi@scilifelab.se\n")
    slurm_handle.write("#SBATCH --mail-type=ALL\n")
    
    slurm_handle.write("\n\n");
    slurm_handle.write("module load abyss/1.3.5\n");
    slurm_handle.write("python ~/assembly_pipeline/de_novo_scilife/script/deNovo_pipeline.py --global-config {} --sample-config {}\n\n".format(global_config,sample_config))
    slurm_handle.close()
    
    command=("sbatch", slurm_file)
    print command
    subprocess.call(command)
    



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample-data-dir', help="full path to directory containing one folder per sample. Each sample contaains only one library (i.e., one PE lib)", type=str)
    parser.add_argument('--genomeSize', help="genome size", type=str)
    parser.add_argument('--orientation', help="I assume I am working only with PE (if not manual editing is needed)", type=str)
    parser.add_argument('--insert', help="I assume that all samples have the same insert (if not manual editing is needed)", type=str)
    parser.add_argument('--std', help="I assume tha all sample have same std (if not manual editing is needed)", type=str)
    parser.add_argument('--kmer', help="kmer to use", type=str)
    parser.add_argument('--global-config', help='foo help')
    
    args = parser.parse_args()

    main(args)