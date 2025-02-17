####################################################
##      				 PorthoMCL
## -------------------------------------------------
## This is a sample PBS Script to run BLASTs for 
## multiple input files against a single database
## 
## You need to update all the variable in enclosed 
## in [] for your PBS script
##
## Once this script is complete, you must be able to 
## submit the job using 
##		qsub porthomclRunPBS.sh
## 
## Ehsan Tabari
#################################################### 

## #PBS lines are not comments. PBS uses these as commands. 
## read more about it on openpbs.org 
##

## This is the Queue name variable. Where to submit the job to? 
## 
#PBS -q [QUEUE_NAME]

## This will indicate the indices of the input to run. 1-100 maybe?
##
#PBS -t 1-12

## Job Name: give it a good name so that you recognize it among the jobs running in the cluster.
## example: #PBS -N 3_porthomcl_run_blast
##
#PBS -N x_porthomcl

## Resource Requirements: I prefer to run each BLAST multithreaded as well. (-num_threads 8) so I ask for 8 cores.
## but for other proceses, you could just use ppm=1
##
#PBS -l nodes=1:ppn=8
#PBS -l walltime=100:00:00

## redirect errors and outputs
## 
#PBS -e /dev/null
#PBS -o /dev/null


### ----------------------------------------
###   IMPORTANT VARIABLE SETTING
### ----------------------------------------
### Make variables for Job names and job log files
###
SHORT_JOBID=`echo $PBS_JOBID |cut -d. -f1`
SHORTER_JOBID=`echo $PBS_JOBID | sed  's/\([0-9]\+\).*/\1/g'`
ORG_JOBNAME=`echo $PBS_JOBNAME |cut -d- -f1`
JOB_FILE=$ORG_JOBNAME-$SHORTER_JOBID-$PBS_ARRAYID
exec 1>$PBS_O_WORKDIR/$JOB_FILE.out  2>$PBS_O_WORKDIR/$JOB_FILE.err


### ----------------------------------------
###   IMPORTANT VARIABLE SETTING
### ----------------------------------------
### This is the folder where you keep your data 
### This is going to be big.
### SKIP the / at the end of it
### example: ROOTFOLDER=/users/<USERNAME>/porthomcl/data
##
ROOTFOLDER=sample



cd $PBS_O_WORKDIR

### ----------------------------------------
###   IMPORTANT VARIABLE SETTING
### ----------------------------------------
### Get the name of the Taxon file to work on based on the job array id:
###
TAXON_FILE="`sed -n $PBS_ARRAYID\p $ROOTFOLDER/taxon_list`"


### ----------------------------------------
###   IMPORTANT STEP TO LOG RUN TIME
### ----------------------------------------
### log the index, taxon id and time of the start
###
echo "$PBS_ARRAYID|$TAXON_FILE|$(date)|start" >> $PBS_O_WORKDIR/$ORG_JOBNAME-$SHORTER_JOBID.timing


############################################
### STEP 3: run the blast
###
### 
### note that -num_threads 8 is passed, adjust it accordingly to your nodes.
###
#
#  mkdir $ROOTFOLDER/3.blastres
#  blastp -query $ROOTFOLDER/3.blastquery/$TAXON_FILE.fasta  -db $ROOTFOLDER/3.blastdb/goodProteins.fasta  -seg yes  -dbsize 100000000  -evalue 1e-5  -outfmt 6 -num_threads 8 -out $ROOTFOLDER/3.blastres/$TAXON_FILE.tab


############################################
### STEP 4: Parse the blast
###
### 
###
#
#  mkdir $ROOTFOLDER/4.splitSimSeq
#
#  porthomclBlastParser $ROOTFOLDER/3.blastresmerge/$TAXON_FILE.tab $ROOTFOLDER/1.compliantFasta >> $ROOTFOLDER/5.splitSimSeq/$TAXON_FILE.ss.tsv



############################################
### STEP 5: Finding Best Hits
###
### 
###
#
#  mkdir $ROOTFOLDER/5.paralogTemp
#  mkdir $ROOTFOLDER/5.besthit
#
#  porthomclPairsBestHit.py -t $ROOTFOLDER/taxon_list -i $ROOTFOLDER/5.input/ -b $ROOTFOLDER/5.besthit -q $ROOTFOLDER/5.bestquerytaxon  -l $JOB_FILE.log -x $PBS_ARRAYID



############################################
### STEP 6: Finding Orthologs
###
### 
###
#
#  mkdir $ROOTFOLDER/6.orthologs
#
#  porthomclPairsOrthologs.py -t $ROOTFOLDER/taxon_list -b $ROOTFOLDER/5.besthit -o $ROOTFOLDER/6.orthologs -l $JOB_FILE.log -x $PBS_ARRAYID



############################################
### STEP 7: Finding Paralogs
###
### 
###


#########
###
### Step 7.1: Find the ogenes:
###
#
#  mkdir $ROOTFOLDER/7.ogenes
#
#  awk -F'[|\t]' '{print $4 >> ("'"$ROOTFOLDER"'/7.ogenes/"$3".og.tsv")}' $ROOTFOLDER/6.orthologs/$TAXON_FILE.ort.tsv 
#  awk -F'[|\t]' '{print $2 >> ("'"$ROOTFOLDER"'/7.ogenes/"$1".og.tsv")}' $ROOTFOLDER/6.orthologs/$TAXON_FILE.ort.tsv 


#########
###
### Step 7.2: Run the paralog
###
#
#  mkdir $ROOTFOLDER/7.paralogs
#
#  porthomclPairsInParalogs.py -t $ROOTFOLDER/taxon_list -q $ROOTFOLDER/5.paralogTemp -o $ROOTFOLDER/7.ogenes -p $ROOTFOLDER/7.paralogs -l $JOB_FILE.log -x $PBS_ARRAYID



############################################
### STEP 8: Run MCL
###
### note that -t 8 is passed, adjust it accordingly to your nodes.
###
#
#  cat $ROOTFOLDER/6.orthologs/*.tsv >> $ROOTFOLDER/8.all.ort.tsv
#
#  mcl $ROOTFOLDER/8.all.ort.tsv  --abc -I 1.5 -t 8 -o $ROOTFOLDER/8.all.ort.group
#
#
#
#  cat $ROOTFOLDER/7.paralogs/*.tsv >> $ROOTFOLDER/8.all.par.tsv
#
#  mcl $ROOTFOLDER/8.all.par.tsv  --abc -I 1.5 -t 8 -o $ROOTFOLDER/8.all.par.group
#


### ----------------------------------------
###   IMPORTANT STEP TO LOG RUN TIME
### ----------------------------------------
### log the index, taxon id and time of the finish
###
echo "$PBS_ARRAYID|$TAXON_FILE|$(date)|end" >> $PBS_O_WORKDIR/$ORG_JOBNAME-$SHORTER_JOBID.timing

