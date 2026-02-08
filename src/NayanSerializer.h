#ifndef NAYANSERIALIZER_H
#define NAYANSERIALIZER_H

#include <optional>
using std::optional;

// These annotations are used by the preprocessing scripts
// They are written as //@AnnotationName in source files
// After processing, they become /*@AnnotationName*/ to be ignored
// Examples: //@Serializable, //@NotNull, //@NotBlank, //@NotEmpty

#include <ArduinoJson.h>
#include <StandardDefines.h>
#include "SerializationUtility.h"
#include "ValidationIncludes.h"

#endif // NAYANSERIALIZER_H
