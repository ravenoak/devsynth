#!/bin/bash
# Script to identify and fix documentation issues in Markdown files
# - Find files with outdated "last_reviewed" dates
# - Find files with incorrect "Implementation Status" notes
# - Update "last_reviewed" dates to current date
# - Remove incorrect "Implementation Status" notes
# - Ensure consistency between "Last updated" dates and "last_reviewed" dates

# Set the current date
CURRENT_DATE=$(date +"%Y-%m-%d")
CURRENT_DATE_FORMATTED=$(date +"%B %-d, %Y")

# Directory to search for Markdown files
DOCS_DIR="docs"

# Function to find files with outdated "last_reviewed" dates
find_outdated_last_reviewed() {
  echo "Files with outdated 'last_reviewed' dates:"
  grep -r "last_reviewed:" --include="*.md" $DOCS_DIR | grep -v "$CURRENT_DATE" | sort
  echo ""
}

# Function to find files with incorrect "Implementation Status" notes
find_implementation_status_notes() {
  echo "Files with 'Implementation Status' notes:"
  grep -r -A 2 "## Implementation Status" --include="*.md" $DOCS_DIR | sort
  echo ""
}

# Function to find files with "Last updated" dates that don't match "last_reviewed" dates
find_inconsistent_dates() {
  echo "Files with inconsistent 'Last updated' and 'last_reviewed' dates:"
  for file in $(find $DOCS_DIR -name "*.md"); do
    last_reviewed=$(grep "last_reviewed:" $file | sed 's/.*last_reviewed: "\(.*\)".*/\1/')
    last_updated=$(grep -i "Last updated:" $file | sed 's/.*Last updated: \(.*\)/\1/')

    if [ -n "$last_reviewed" ] && [ -n "$last_updated" ]; then
      if [ "$last_reviewed" != "$last_updated" ]; then
        echo "$file: last_reviewed=$last_reviewed, last_updated=$last_updated"
      fi
    fi
  done
  echo ""
}

# Function to update "last_reviewed" dates to current date
update_last_reviewed() {
  if [ "$1" == "--dry-run" ]; then
    echo "DRY RUN: Files that would have 'last_reviewed' dates updated to $CURRENT_DATE:"
    grep -l "last_reviewed:" --include="*.md" $DOCS_DIR | sort
  else
    echo "Updating 'last_reviewed' dates to $CURRENT_DATE..."
    for file in $(grep -l "last_reviewed:" --include="*.md" $DOCS_DIR); do
      sed -i '' "s/last_reviewed: \"[^\"]*\"/last_reviewed: \"$CURRENT_DATE\"/" $file
      echo "Updated: $file"
    done
  fi
  echo ""
}

# Function to remove incorrect "Implementation Status" notes
remove_implementation_status() {
  if [ "$1" == "--dry-run" ]; then
    echo "DRY RUN: Files that would have 'Implementation Status' notes removed:"
    grep -l -A 2 "## Implementation Status" --include="*.md" $DOCS_DIR | sort
  else
    echo "Removing 'Implementation Status' notes..."
    for file in $(grep -l "## Implementation Status" --include="*.md" $DOCS_DIR); do
      # Create a temporary file
      tmp_file=$(mktemp)

      # Remove the Implementation Status section and everything after it
      sed '/## Implementation Status/,$d' $file > $tmp_file

      # Add a newline at the end if needed
      echo "" >> $tmp_file

      # Replace the original file with the modified content
      mv $tmp_file $file

      echo "Updated: $file"
    done
  fi
  echo ""
}

# Function to update "Last updated" dates to match "last_reviewed" dates
update_last_updated() {
  if [ "$1" == "--dry-run" ]; then
    echo "DRY RUN: Files that would have 'Last updated' dates updated to match 'last_reviewed' dates:"
    for file in $(grep -l "last_reviewed:" --include="*.md" $DOCS_DIR); do
      if grep -q -i "Last updated:" $file; then
        echo "$file"
      fi
    done
  else
    echo "Updating 'Last updated' dates to match 'last_reviewed' dates..."
    for file in $(grep -l "last_reviewed:" --include="*.md" $DOCS_DIR); do
      if grep -q -i "Last updated:" $file; then
        last_reviewed=$(grep "last_reviewed:" $file | sed 's/.*last_reviewed: "\(.*\)".*/\1/')
        formatted_date=$(date -j -f "%Y-%m-%d" "$last_reviewed" "+%B %-d, %Y" 2>/dev/null)

        if [ -n "$formatted_date" ]; then
          sed -i '' "s/_Last updated:.*/_Last updated: $formatted_date/" $file
          echo "Updated: $file"
        fi
      fi
    done
  fi
  echo ""
}

# Main function
main() {
  case "$1" in
    find)
      find_outdated_last_reviewed
      find_implementation_status_notes
      find_inconsistent_dates
      ;;
    update-last-reviewed)
      update_last_reviewed "$2"
      ;;
    remove-implementation-status)
      remove_implementation_status "$2"
      ;;
    update-last-updated)
      update_last_updated "$2"
      ;;
    fix-all)
      if [ "$2" == "--dry-run" ]; then
        update_last_reviewed "--dry-run"
        remove_implementation_status "--dry-run"
        update_last_updated "--dry-run"
      else
        update_last_reviewed
        remove_implementation_status
        update_last_updated
      fi
      ;;
    *)
      echo "Usage: $0 [command] [options]"
      echo ""
      echo "Commands:"
      echo "  find                         Find documentation issues"
      echo "  update-last-reviewed         Update 'last_reviewed' dates to current date"
      echo "  remove-implementation-status Remove incorrect 'Implementation Status' notes"
      echo "  update-last-updated          Update 'Last updated' dates to match 'last_reviewed' dates"
      echo "  fix-all                      Apply all fixes"
      echo ""
      echo "Options:"
      echo "  --dry-run                    Show what would be done without making changes"
      ;;
  esac
}

# Run the main function with all arguments
main "$@"
