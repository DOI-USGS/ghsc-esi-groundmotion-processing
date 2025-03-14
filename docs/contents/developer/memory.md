# Memory tracking

You can use the `malloctrace` standard Python module to track memory usage.
The `gmprocess.utils.memory` module includes helper functions for displaying memory usage and lines where the largest allocations occur.

## Example

```python
import tracemalloc
from gmprocess.utils import memory

tracemalloc.start()
memory.display_total(message="start")

# Lots of code...

memory.display_mallocs(message="end", snapshot=tracemalloc.take_snapshot())
```
