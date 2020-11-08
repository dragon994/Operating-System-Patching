#!/bin/bash
RELEASE="$(lsb_release -d | tr '\t' ' ' | cut -d " " -f 2-)"
SUPPORTED=false
LATEST=false
packages_up_to_date=true
echo "<version>$RELEASE</version>" > extracted_data.txt
while read version; do
	if [ "$version" = "$(echo $RELEASE | cut -d ' ' -f -2 | cut -d '.' -f -2)" ]
  then 
	  SUPPORTED=true
	  echo "<supported>1</supported>" >> extracted_data.txt
  fi
done <supported_versions.txt

while read release; do
	if [ "$release" = "$RELEASE" ] 
	then
		LATEST=true
		echo "<latest>1</latest>" >> extracted_data.txt
	fi
done <latest_releases.txt

if [ "$SUPPORTED" = false ] 
then
	echo "<supported>0</supported>" >> extracted_data.txt
elif [ "$LATEST" = false ]
then
	echo "<latest>0</latest>" >> extracted_data.txt
else
	FILE="sec_notices/$(echo $RELEASE | cut -d ' ' -f -2 | cut -d '.' -f -2 | cut -d " " -f 2-)"
	$(mkdir temp)
	$(cp -r /var/log/apt/history.log* ./temp)
	$(gunzip temp/history.log.*)
	latest=0
	updated=0
	update_released=0
	while read line; do
		version="$(echo $line | cut -d ' ' -f 2)"
		package="$(echo $line | cut -d ' ' -f 1)"
		if [ $version = $package ]
		then
			update_released=$line
		else
			installed_version=$(apt-cache policy $package | grep Installed | cut -d " " -f 4)
			candidate=$(apt-cache policy $package | grep Candidate | cut -d " " -f 4)
			if [ "$installed_version" != "$candidate" ] || [ "$installed_version" != "$version" ]
			then 
				packages_up_to_date=false
				echo "<packagesupdated>0</packagesupdated>" >> extracted_data.txt
				break
			else
				date=$(grep -B 2 "$package" temp/history.log* | grep -B 2 "$version" | grep Start | cut -d " " -f 2)
				date_num=$(echo $date | tr -d "-")
				if [ $latest = 0 ] || [ $date_num -gt $latest ]
				then
					latest=$date_num
					updated=$date
				fi

			fi
		fi
	done <$FILE
	if [ "$packages_up_to_date" = true ]
	then	
		echo "<packagesupdated>1</packagesupdated>" >> extracted_data.txt
	fi
	$(rm -r temp)
	days=$(( $(date +%s --date "$updated")/(24*60*60) - $(date +%s --date "$update_released")/(24*60*60) ))
	echo "<days>$days</days>" >> extracted_data.txt
fi