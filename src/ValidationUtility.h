#ifndef DTO_VALIDATION_UTILITY_H
#define DTO_VALIDATION_UTILITY_H

#include <ArduinoJson.h>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <list>
#include <deque>
#include <array>
#include <type_traits>

namespace nayan {
namespace validation {

/**
 * Utility class for DTO validation.
 * Provides static methods for validating NotNull and NotBlank constraints.
 * Uses generic document type to support different JSON/document implementations.
 */
class ValidationUtility {
public:
    /**
     * Validate that a field is not null in the document.
     * 
     * @tparam DocType The document type (e.g., JsonDocument, or future document types)
     * @tparam Args Optional variadic arguments for future extensibility
     * @param doc The document (generic type, currently JsonDocument)
     * @param fieldName The name of the field to validate
     * @param validationErrors String to append error messages to (if validation fails)
     * @param args Optional variadic arguments for future extensibility
     * @return true if validation passes, false if validation fails
     */
    template<typename DocType, typename... Args>
    static bool ValidateNotNull(DocType& doc, const char* fieldName, StdString& validationErrors, Args... args) {
        // Variadic args are available for future use but currently ignored
        (void)(sizeof...(args)); // Suppress unused parameter warning
        
        // For now, assume DocType has JsonDocument-like interface (isNull(), operator[])
        // In future, this can be specialized for different document types
        if (doc[fieldName].isNull()) {
            if (!validationErrors.empty()) validationErrors += ",\n";
            validationErrors += "NotNull field '";
            validationErrors += fieldName;
            validationErrors += "' is required but was null or missing";
            return false;
        }
        return true;
    }

    /**
     * Validate that a string field is not blank (not empty after trimming whitespace).
     * Also validates that the field is not null.
     * 
     * @tparam DocType The document type (e.g., JsonDocument, or future document types)
     * @tparam Args Optional variadic arguments for future extensibility
     * @param doc The document (generic type, currently JsonDocument)
     * @param fieldName The name of the field to validate
     * @param validationErrors String to append error messages to (if validation fails)
     * @param args Optional variadic arguments for future extensibility
     * @return true if validation passes, false if validation fails
     */
    template<typename DocType, typename... Args>
    static bool ValidateNotBlank(DocType& doc, const char* fieldName, StdString& validationErrors, Args... args) {
        // Variadic args are available for future use but currently ignored
        (void)(sizeof...(args)); // Suppress unused parameter warning
        
        // For now, assume DocType has JsonDocument-like interface (isNull(), operator[], as<>())
        // In future, this can be specialized for different document types
        // First check if field is null
        if (doc[fieldName].isNull()) {
            if (!validationErrors.empty()) validationErrors += ",\n";
            validationErrors += "NotBlank field '";
            validationErrors += fieldName;
            validationErrors += "' is required but was null or missing";
            return false;
        }
        
        // Get the string value
        StdString fieldValue = doc[fieldName].template as<const char*>();
        
        // Trim whitespace (spaces, tabs, newlines, carriage returns)
        StdString trimmed = fieldValue;
        // Trim leading whitespace
        size_t start = trimmed.find_first_not_of(" \t\n\r");
        if (start != StdString::npos) {
            trimmed.erase(0, start);
        } else {
            // String contains only whitespace
            trimmed.clear();
        }
        
        // Trim trailing whitespace
        if (!trimmed.empty()) {
            size_t end = trimmed.find_last_not_of(" \t\n\r");
            if (end != StdString::npos) {
                trimmed.erase(end + 1);
            } else {
                trimmed.clear();
            }
        }
        
        // Check if trimmed string is empty
        if (trimmed.empty()) {
            if (!validationErrors.empty()) validationErrors += ",\n";
            validationErrors += "NotBlank field '";
            validationErrors += fieldName;
            validationErrors += "' cannot be empty or blank";
            return false;
        }
        
        return true;
    }

    /**
     * Validate that a field is not empty.
     * Works for strings, arrays, collections (vector, list, set, deque), and maps.
     * Similar to Java's @NotEmpty annotation.
     * Also validates that the field is not null.
     * 
     * @tparam DocType The document type (e.g., JsonDocument, or future document types)
     * @tparam Args Optional variadic arguments for future extensibility (e.g., type hint)
     * @param doc The document (generic type, currently JsonDocument)
     * @param fieldName The name of the field to validate
     * @param validationErrors String to append error messages to (if validation fails)
     * @param args Optional variadic arguments for future extensibility
     * @return true if validation passes, false if validation fails
     */
    template<typename DocType, typename... Args>
    static bool ValidateNotEmpty(DocType& doc, const char* fieldName, StdString& validationErrors, Args... args) {
        // Variadic args are available for future use but currently ignored
        (void)(sizeof...(args)); // Suppress unused parameter warning
        
        // For now, assume DocType has JsonDocument-like interface (isNull(), operator[], as<>(), is<>())
        // In future, this can be specialized for different document types
        
        // First check if field is null
        if (doc[fieldName].isNull()) {
            if (!validationErrors.empty()) validationErrors += ",\n";
            validationErrors += "NotEmpty field '";
            validationErrors += fieldName;
            validationErrors += "' is required but was null or missing";
            return false;
        }
        
        // Check if it's a string
        if (doc[fieldName].template is<const char*>() || doc[fieldName].template is<StdString>()) {
            StdString fieldValue = doc[fieldName].template as<const char*>();
            if (fieldValue.empty()) {
                if (!validationErrors.empty()) validationErrors += ",\n";
                validationErrors += "NotEmpty field '";
                validationErrors += fieldName;
                validationErrors += "' cannot be empty";
                return false;
            }
            return true;
        }
        
        // Check if it's a JSON array (vector, list, set, deque, array, or C-style array)
        if (doc[fieldName].template is<JsonArray>()) {
            JsonArray arr = doc[fieldName].template as<JsonArray>();
            if (arr.size() == 0) {
                if (!validationErrors.empty()) validationErrors += ",\n";
                validationErrors += "NotEmpty field '";
                validationErrors += fieldName;
                validationErrors += "' (array/collection) cannot be empty";
                return false;
            }
            return true;
        }
        
        // Check if it's a JSON object (map)
        if (doc[fieldName].template is<JsonObject>()) {
            JsonObject obj = doc[fieldName].template as<JsonObject>();
            if (obj.size() == 0) {
                if (!validationErrors.empty()) validationErrors += ",\n";
                validationErrors += "NotEmpty field '";
                validationErrors += fieldName;
                validationErrors += "' (map) cannot be empty";
                return false;
            }
            return true;
        }
        
        // For other types, try to check if they have a size() method or length
        // This handles cases where the type might be detected differently
        // If we can't determine, assume it's valid (to avoid false positives)
        // In future, variadic args could be used to specify the expected type
        
        return true;
    }
};

} // namespace validation
} // namespace nayan

#endif // DTO_VALIDATION_UTILITY_H

