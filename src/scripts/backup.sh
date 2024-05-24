#!/bin/bash

#
#### Project backup script
#

echo ""
echo "Project backup script"
echo ""

# 1. Get script directory
dir_script="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
path_exclusion_list="$dir_script/exclusion-list.txt"
echo "Script directory: '$dir_script'"
echo "Exclusion list path: '$path_exclusion_list'"
echo ""
# print exclusion list lines
echo "Exclusion list:"
cat $path_exclusion_list
echo ""
echo ""

# 2. Move to script directory and then move up until you reach the project root ("masters-thesis") and then one more time
function move_to_project_root {
	while [ $(basename "$PWD") != "masters-thesis" ]; do
		cd ..
	done
}

echo "Moving to script directory..."
cd $dir_script
echo "Moving to project root parent directory..."
move_to_project_root
cd ..
echo "cwd at '$PWD'"
echo ""

# 3. Create archive (7z with maximum compression) and move it to the backup folder (masters-thesis-backups)
timestamp=$(date +%F) # format: YYYY-MM-DD
backup_folder="masters-thesis-$timestamp"
path_archive="$backup_folder.7z"
num_threads=$(nproc)
# make the number of threads number of threads - 2 if it is greater than 2 otherwise 1
num_threads=$(($num_threads > 2 ? $num_threads - 2 : 1))
# echo "Archive settings: '$path_archive' with $num_threads threads..."
echo "Archive settings: '7z a -t7z -m0=lzma2 -mx=9 -mfb=64 -md=32m -ms=on -mmt=$num_threads -x@\"$path_exclusion_list\" \"$path_archive\" masters-thesis'"
echo ""
read -p "Use exclusion list for this archive? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
	echo "Creating archive with exclusion list..."
	echo ""
	7z a -t7z -m0=lzma2 -mx=9 -mfb=64 -md=32m -ms=on -mmt=$num_threads -x@"$path_exclusion_list" "$path_archive" masters-thesis
else
	echo "Creating archive (complete backup)"
	echo ""
	7z a -t7z -m0=lzma2 -mx=9 -mfb=64 -md=32m -ms=on -mmt=$num_threads "$path_archive" masters-thesis 
fi
echo ""
echo ""
if [ ! -f "$path_archive" ]; then
	echo "Archive was not created. Exiting..."
	exit 1
fi
echo "Done creating archive."
echo ""

# 4. Move archive to backups folder
echo "Moving archive to masters-thesis-backups folder..."
echo ""
mv $path_archive masters-thesis-backups
echo ""
echo ""
echo "Archive moved to masters-thesis-backups folder."
echo ""
echo "Done."