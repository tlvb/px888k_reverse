left="$1"
right="$2"
shift 2
vimdiff "$@" <(xxd "$left") <(xxd "$right")
