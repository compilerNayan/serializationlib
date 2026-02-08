#ifndef SERIALIZATION_UTILITY_H
#define SERIALIZATION_UTILITY_H

#include <StandardDefines.h>
#include <ArduinoJson.h>
#include <string>
#include <sstream>
#include <type_traits>
#include <stdexcept>
#include <algorithm>
#include <cctype>
#include <vector>
#include <list>
#include <deque>
#include <set>
#include <unordered_set>
#include <map>
#include <unordered_map>
#include <array>
#include <forward_list>

namespace nayan {
namespace serializer {

/**

 * Generic Serialization Utility
 * Provides a static template method to serialize any type.
 * 
 * For primitive types (int, char, bool, float, double, and types from StandardDefines),
 * converts the value to StdString.
 * 
 * For non-primitive types, calls the type's Serialize() method.
 */
class SerializationUtility {
public:
    /**
     * Serialize a value to StdString.
     * 
     * @tparam T The type to serialize
     * @param value The value to serialize
     * @return StdString representation of the value
     */
    template<typename T>
    static StdString Serialize(const T& value) {
        if constexpr (is_optional_type_v<T>) {
            // Handle optional types (optional<T> or std::optional<T>)
            if (value.has_value()) {
                // If optional has a value, serialize it
                return Serialize(value.value());
            } else {
                // If optional is empty, return empty JSON string
                return "";
            }
        } else if constexpr (is_primitive_type_v<T>) {
            // Convert primitive type to string
            return convert_primitive_to_string(value);
        } else if constexpr (is_sequential_container_v<T>) {
            // Handle sequential containers (vector, list, deque, set, unordered_set, etc.)
            return serialize_sequential_container(value);
        } else if constexpr (is_associative_container_v<T>) {
            // Handle associative containers (map, unordered_map)
            return serialize_associative_container(value);
        } else if constexpr (std::is_enum_v<T>) {
            // Handle enum types - template specialization should be provided by S8_handle_enum_serialization.py
            // If no specialization exists, this will cause a compilation error
            // We can't call value.Serialize() because enums don't have that method
            // The specialization must exist for enums to work
            // Use a dependent static_assert that only fails when T is an enum
            static_assert(std::is_enum_v<T> && false, "Enum serialization specialization not found. Run S8_handle_enum_serialization.py for this enum.");
            return StdString(); // This line will never be reached due to static_assert
        } else {
            // Call the type's Serialize method
            return value.Serialize();
        }
    }

    /**
     * Deserialize a string to a value of the specified type.
     * 
     * @tparam ReturnType The type to deserialize to
     * @param input The string input to deserialize
     * @return The deserialized value of type ReturnType
     */
    template<typename ReturnType>
    static ReturnType Deserialize(const StdString& input) {
        if constexpr (is_optional_type_v<ReturnType>) {
            // Handle optional types (optional<T> or std::optional<T>)
            using ValueType = typename ReturnType::value_type;
            
            // Check if input is null or empty
            if (input.empty() || input == "null" || input == "{}") {
                return ReturnType(); // Return empty optional
            }
            
            // Try to parse as JSON to check if it's null
            JsonDocument doc;
            DeserializationError error = deserializeJson(doc, input.c_str());
            if (error == DeserializationError::Ok && doc.isNull()) {
                return ReturnType(); // Return empty optional
            }
            
            // If parsing succeeded, extract the value from JSON
            ValueType value;
            if (error == DeserializationError::Ok) {
                // For primitive types, extract directly from JSON
                if constexpr (is_primitive_type_v<ValueType>) {
                    if constexpr (std::is_same_v<ValueType, StdString> || std::is_same_v<ValueType, CStdString>) {
                        // For strings, extract from JSON (handles quoted strings like "Hello World")
                        if (doc.is<const char*>() || doc.is<StdString>()) {
                            const char* str = doc.as<const char*>();
                            if (str != nullptr) {
                                value = StdString(str);
                            } else {
                                value = Deserialize<ValueType>(input);
                            }
                        } else {
                            value = Deserialize<ValueType>(input);
                        }
                    } else {
                        // For other primitives, use JSON extraction
                        if (doc.is<ValueType>()) {
                            value = doc.as<ValueType>();
                        } else {
                            value = Deserialize<ValueType>(input);
                        }
                    }
                } else {
                    // For complex types, serialize JSON back to string and deserialize
                    StdString jsonStr;
                    serializeJson(doc, jsonStr);
                    value = Deserialize<ValueType>(jsonStr);
                }
            } else {
                // If JSON parsing failed, try direct deserialization
                value = Deserialize<ValueType>(input);
            }
            
            return ReturnType(value);
        } else if constexpr (is_primitive_type_v<ReturnType>) {
            // Convert string to primitive type
            return convert_string_to_primitive<ReturnType>(input);
        } else if constexpr (is_sequential_container_v<ReturnType>) {
            // Handle sequential containers (vector, list, deque, set, unordered_set, etc.)
            return deserialize_sequential_container<ReturnType>(input);
        } else if constexpr (is_associative_container_v<ReturnType>) {
            // Handle associative containers (Map, UnorderedMap)
            return deserialize_associative_container<ReturnType>(input);
        } else if constexpr (std::is_enum_v<ReturnType>) {
            // Handle enum types - template specialization should be provided by S8_handle_enum_serialization.py
            // If no specialization exists, this will cause a compilation error
            // We can't call ReturnType::Deserialize() because enums don't have that method
            // The specialization must exist for enums to work
            // Use a dependent static_assert that only fails when ReturnType is an enum
            static_assert(std::is_enum_v<ReturnType> && false, "Enum deserialization specialization not found. Run S8_handle_enum_serialization.py for this enum.");
            return ReturnType(); // This line will never be reached due to static_assert
        } else {
            // Call the type's Deserialize method
            return ReturnType::Deserialize(input);
        }
    }

    // Make is_primitive_type accessible to helper functions
    template<typename T>
    struct is_primitive_type {
        static constexpr bool value = 
            std::is_same_v<T, int> || std::is_same_v<T, unsigned int> ||
            std::is_same_v<T, long> || std::is_same_v<T, unsigned long> ||
            std::is_same_v<T, short> || std::is_same_v<T, unsigned short> ||
            std::is_same_v<T, char> || std::is_same_v<T, unsigned char> ||
            std::is_same_v<T, bool> || std::is_same_v<T, float> ||
            std::is_same_v<T, double> || std::is_same_v<T, size_t> ||
            // StandardDefines types
            std::is_same_v<T, Int> || std::is_same_v<T, CInt> ||
            std::is_same_v<T, UInt> || std::is_same_v<T, CUInt> ||
            std::is_same_v<T, Long> || std::is_same_v<T, CLong> ||
            std::is_same_v<T, ULong> || std::is_same_v<T, CULong> ||
            std::is_same_v<T, UInt8> ||
            std::is_same_v<T, Char> || std::is_same_v<T, CChar> ||
            std::is_same_v<T, UChar> || std::is_same_v<T, CUChar> ||
            std::is_same_v<T, Bool> || std::is_same_v<T, CBool> ||
            std::is_same_v<T, Size> || std::is_same_v<T, CSize> ||
            std::is_same_v<T, StdString> || std::is_same_v<T, CStdString>;
    };
    
    // Helper variable template
    template<typename T>
    static constexpr bool is_primitive_type_v = is_primitive_type<T>::value;
    
    /**
     * Type trait to check if a type is a sequential container.
     * Includes: vector, list, deque, set, unordered_set, array, forward_list
     */
    template<typename T>
    struct is_sequential_container {
        static constexpr bool value = false;
    };
    
    template<typename T, typename Alloc>
    struct is_sequential_container<std::vector<T, Alloc>> {
        static constexpr bool value = true;
    };
    
    template<typename T, typename Alloc>
    struct is_sequential_container<std::list<T, Alloc>> {
        static constexpr bool value = true;
    };
    
    template<typename T, typename Alloc>
    struct is_sequential_container<std::deque<T, Alloc>> {
        static constexpr bool value = true;
    };
    
    template<typename T, typename Compare, typename Alloc>
    struct is_sequential_container<std::set<T, Compare, Alloc>> {
        static constexpr bool value = true;
    };
    
    template<typename T, typename Hash, typename Equal, typename Alloc>
    struct is_sequential_container<std::unordered_set<T, Hash, Equal, Alloc>> {
        static constexpr bool value = true;
    };
    
    template<typename T, std::size_t N>
    struct is_sequential_container<std::array<T, N>> {
        static constexpr bool value = true;
    };
    
    template<typename T, typename Alloc>
    struct is_sequential_container<std::forward_list<T, Alloc>> {
        static constexpr bool value = true;
    };
    
    // Note: StandardDefines typedefs (vector, list, etc.) and template aliases (Vector, List, etc.)
    // all resolve to std:: types, so they are handled by the std:: specializations above.
    // No additional specializations are needed since template aliases don't create new types.
    
    
    // Helper variable template
    template<typename T>
    static constexpr bool is_sequential_container_v = is_sequential_container<T>::value;
    
    /**
     * Type trait to check if a type is an associative container (map).
     * Includes: map, unordered_map, multimap, unordered_multimap
     */
    template<typename T>
    struct is_associative_container {
        static constexpr bool value = false;
    };
    
    template<typename Key, typename Value, typename Compare, typename Alloc>
    struct is_associative_container<std::map<Key, Value, Compare, Alloc>> {
        static constexpr bool value = true;
    };
    
    template<typename Key, typename Value, typename Hash, typename Equal, typename Alloc>
    struct is_associative_container<std::unordered_map<Key, Value, Hash, Equal, Alloc>> {
        static constexpr bool value = true;
    };
    
    template<typename Key, typename Value, typename Compare, typename Alloc>
    struct is_associative_container<std::multimap<Key, Value, Compare, Alloc>> {
        static constexpr bool value = true;
    };
    
    template<typename Key, typename Value, typename Hash, typename Equal, typename Alloc>
    struct is_associative_container<std::unordered_multimap<Key, Value, Hash, Equal, Alloc>> {
        static constexpr bool value = true;
    };
    
    // Handle StandardDefines typedefs (Map, UnorderedMap)
    template<typename Key, typename Value>
    struct is_associative_container<Map<Key, Value>> {
        static constexpr bool value = true;
    };
    
    template<typename Key, typename Value>
    struct is_associative_container<UnorderedMap<Key, Value>> {
        static constexpr bool value = true;
    };
    
    // Helper variable template
    template<typename T>
    static constexpr bool is_associative_container_v = is_associative_container<T>::value;
    
    /**
     * Type trait to check if a type is an optional type (std::optional<T> or optional<T>).
     */
    template<typename T>
    struct is_optional_type {
        static constexpr bool value = false;
    };
    
    template<typename T>
    struct is_optional_type<std::optional<T>> {
        static constexpr bool value = true;
    };
    
    // Helper variable template
    template<typename T>
    static constexpr bool is_optional_type_v = is_optional_type<T>::value;
    
    /**
     * Convert a primitive type to StdString.
     * Uses overloads for special cases.
     */
    template<typename T>
    static StdString convert_primitive_to_string(const T& value) {
        if constexpr (std::is_same_v<T, bool> || std::is_same_v<T, Bool> || std::is_same_v<T, CBool>) {
            return value ? "true" : "false";
        } else if constexpr (std::is_same_v<T, StdString>) {
            return value;
        } else if constexpr (std::is_same_v<T, CStdString>) {
            return StdString(value);
        } else {
            std::ostringstream oss;
            oss << value;
            return StdString(oss.str());
        }
    }
    
    /**
     * Convert a string to a primitive type.
     * 
     * @tparam T The primitive type to convert to
     * @param input The string input
     * @return The converted value of type T
     */
    template<typename T>
    static T convert_string_to_primitive(const StdString& input) {
        if constexpr (std::is_same_v<T, bool> || std::is_same_v<T, Bool> || std::is_same_v<T, CBool>) {
            // Handle boolean: "true", "false", "1", "0"
            StdString lower = input;
            std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
            if (lower == "true" || lower == "1") {
                return true;
            } else if (lower == "false" || lower == "0") {
                return false;
            } else {
                throw std::invalid_argument("Invalid boolean value: " + input);
            }
        } else if constexpr (std::is_same_v<T, StdString> || std::is_same_v<T, CStdString>) {
            // Already a string, just return it
            return input;
        } else if constexpr (std::is_integral_v<T>) {
            // Integer types
            try {
                if constexpr (std::is_signed_v<T>) {
                    return static_cast<T>(std::stoll(input));
                } else {
                    return static_cast<T>(std::stoull(input));
                }
            } catch (const std::exception& e) {
                throw std::invalid_argument("Invalid integer value: " + input);
            }
        } else if constexpr (std::is_floating_point_v<T>) {
            // Floating point types
            try {
                return static_cast<T>(std::stod(input));
            } catch (const std::exception& e) {
                throw std::invalid_argument("Invalid floating point value: " + input);
            }
        } else if constexpr (std::is_same_v<T, char> || std::is_same_v<T, Char> || std::is_same_v<T, CChar> ||
                             std::is_same_v<T, unsigned char> || std::is_same_v<T, UChar> || std::is_same_v<T, CUChar> ||
                             std::is_same_v<T, UInt8>) {
            // Character types
            if (input.length() == 1) {
                return static_cast<T>(input[0]);
            } else if (input.length() == 0) {
                return static_cast<T>(0);
            } else {
                // Try to parse as integer for character types
                try {
                    return static_cast<T>(std::stoi(input));
                } catch (const std::exception& e) {
                    throw std::invalid_argument("Invalid character value: " + input);
                }
            }
        } else {
            // Fallback: try to use stringstream
            std::istringstream iss(input);
            T value;
            if (!(iss >> value)) {
                throw std::invalid_argument("Cannot convert string to type: " + input);
            }
            return value;
        }
    }
    
    /**
     * Serialize a sequential container (vector, list, deque, set, etc.) to JSON array.
     */
    template<typename Container>
    static StdString serialize_sequential_container(const Container& container) {
        JsonDocument doc;
        JsonArray array = doc.to<JsonArray>();
        
        // Special handling for vector<bool> which uses a proxy type
        if constexpr (std::is_same_v<Container, std::vector<bool>> || std::is_same_v<Container, vector<bool>>) {
            for (size_t i = 0; i < container.size(); ++i) {
                bool boolValue = container[i];
                array.add(boolValue);
            }
        } else {
            for (const auto& element : container) {
                if constexpr (is_primitive_type_v<typename Container::value_type>) {
                    // For primitives, add directly to array
                    if constexpr (std::is_same_v<typename Container::value_type, bool> || 
                                  std::is_same_v<typename Container::value_type, Bool> ||
                                  std::is_same_v<typename Container::value_type, CBool>) {
                        array.add(element);
                } else if constexpr (std::is_same_v<typename Container::value_type, StdString> ||
                                     std::is_same_v<typename Container::value_type, CStdString> ||
                                     std::is_same_v<typename Container::value_type, std::string>) {
                    array.add(element.c_str());
                } else if constexpr (std::is_integral_v<typename Container::value_type>) {
                    array.add(static_cast<int64_t>(element));
                } else if constexpr (std::is_floating_point_v<typename Container::value_type>) {
                    array.add(static_cast<double>(element));
                } else {
                    // Fallback: serialize and parse
                    StdString elementJson = Serialize(element);
                    JsonDocument elemDoc;
                    if (deserializeJson(elemDoc, elementJson.c_str()) == DeserializationError::Ok) {
                        array.add(elemDoc.as<JsonVariant>());
                    } else {
                        array.add(elementJson.c_str());
                    }
                }
                } else {
                    // For complex types, serialize to JSON string, then parse and add
                    StdString elementJson = Serialize(element);
                    JsonDocument elementDoc;
                    DeserializationError error = deserializeJson(elementDoc, elementJson.c_str());
                    if (error == DeserializationError::Ok) {
                        array.add(elementDoc.as<JsonVariant>());
                    } else {
                        // If parsing fails, add as string (shouldn't happen for valid JSON)
                        array.add(elementJson.c_str());
                    }
                }
            }
        }
        
        StdString output;
        serializeJson(doc, output);
        return StdString(output.c_str());
    }
    
    /**
     * Helper type trait to detect std::array (used for Array alias detection)
     */
    template<typename T>
    struct is_std_array_type : std::false_type {};
    
    template<typename T, std::size_t N>
    struct is_std_array_type<std::array<T, N>> : std::true_type {};
    
    /**
     * Helper function to deserialize a single element from JSON and add it to a container.
     * Handles different container insertion methods (push_back, insert, array indexing).
     */
    template<typename Container, typename ValueType>
    static void deserialize_and_add_element(Container& container, const JsonVariant& element, size_t index) {
        ValueType deserializedValue;
        
        if constexpr (is_primitive_type_v<ValueType>) {
            // For primitive types, extract directly from JSON
            if constexpr (std::is_same_v<ValueType, bool> || 
                         std::is_same_v<ValueType, Bool> || 
                         std::is_same_v<ValueType, CBool>) {
                deserializedValue = element.as<bool>();
            } else if constexpr (std::is_same_v<ValueType, StdString> ||
                                 std::is_same_v<ValueType, CStdString> ||
                                 std::is_same_v<ValueType, std::string>) {
                const char* str = element.as<const char*>();
                deserializedValue = ValueType(str ? str : "");
            } else if constexpr (std::is_integral_v<ValueType>) {
                if constexpr (std::is_signed_v<ValueType>) {
                    deserializedValue = static_cast<ValueType>(element.as<int64_t>());
                } else {
                    deserializedValue = static_cast<ValueType>(element.as<uint64_t>());
                }
            } else if constexpr (std::is_floating_point_v<ValueType>) {
                deserializedValue = static_cast<ValueType>(element.as<double>());
            } else {
                // Fallback for other primitive types
                StdString elementStr;
                serializeJson(element, elementStr);
                deserializedValue = convert_string_to_primitive<ValueType>(elementStr);
            }
        } else if constexpr (std::is_enum_v<ValueType>) {
            // For enums, deserialize from string
            StdString elementStr;
            serializeJson(element, elementStr); // Convert JsonVariant to string
            deserializedValue = SerializationUtility::Deserialize<ValueType>(elementStr);
        } else {
            // For complex types (like ProductX), serialize the element to JSON string
            // and call the type's Deserialize method
            StdString elementJson;
            serializeJson(element, elementJson);
            deserializedValue = ValueType::Deserialize(elementJson);
        }
        
        // Add to container based on container type
        // Helper to detect if container is Set/UnorderedSet
        constexpr bool isSetType = std::is_same_v<Container, std::set<ValueType>> ||
                                  std::is_same_v<Container, Set<ValueType>> ||
                                  std::is_same_v<Container, std::unordered_set<ValueType>> ||
                                  std::is_same_v<Container, UnorderedSet<ValueType>>;
        
        // Helper to detect if container is Array (std::array or Array alias)
        // Since Array<T, N> is an alias for std::array<T, N>, we check for std::array
        constexpr bool isArrayType = std::is_array_v<Container> || 
                                     is_std_array_type<Container>::value;
        
        if constexpr (isSetType) {
            // Set and UnorderedSet use insert
            container.insert(deserializedValue);
        } else if constexpr (isArrayType) {
            // Array uses indexing (fixed size)
            if constexpr (std::is_array_v<Container>) {
                if (index < std::extent_v<Container>) {
                    container[index] = deserializedValue;
                }
            } else {
                // std::array or Array
                if (index < container.size()) {
                    container[index] = deserializedValue;
                }
            }
        } else {
            // Vector, List, Deque use push_back
            container.push_back(deserializedValue);
        }
    }
    
    /**
     * Deserialize a JSON array string to a sequential container.
     * Supports: Vector, List, Deque, Set, UnorderedSet, Array
     * 
     * @tparam Container The container type to deserialize to (e.g., Vector<ProductX>, Set<int>, Array<Person, 3>)
     * @param input The JSON array string
     * @return The deserialized container
     */
    template<typename Container>
    static Container deserialize_sequential_container(const StdString& input) {
        // Parse the JSON string into a JsonDocument
        JsonDocument doc;
        DeserializationError error = deserializeJson(doc, input.c_str());
        
        if (error != DeserializationError::Ok) {
            throw std::invalid_argument("Failed to parse JSON: " + input);
        }
        
        // Check if it's an array
        if (!doc.is<JsonArray>()) {
            throw std::invalid_argument("Expected JSON array, got: " + input);
        }
        
        JsonArray jsonArray = doc.as<JsonArray>();
        Container container;
        
        // Get the value type of the container
        using ValueType = typename Container::value_type;
        
        // Check if it's an Array (fixed size) and validate size
        if constexpr (std::is_array_v<Container>) {
            // C-style array
            constexpr size_t arraySize = std::extent_v<Container>;
            if (jsonArray.size() != arraySize) {
                throw std::invalid_argument("JSON array size (" + std::to_string(jsonArray.size()) + 
                                          ") does not match Array size (" + std::to_string(arraySize) + ")");
            }
        } else if constexpr (is_std_array_type<Container>::value) {
            // std::array or Array - validate size
            constexpr size_t arraySize = std::tuple_size_v<Container>;
            if (jsonArray.size() != arraySize) {
                throw std::invalid_argument("JSON array size (" + std::to_string(jsonArray.size()) + 
                                          ") does not match Array size (" + std::to_string(arraySize) + ")");
            }
        }
        
        // Iterate through each element in the JSON array
        size_t index = 0;
        for (JsonVariant element : jsonArray) {
            deserialize_and_add_element<Container, ValueType>(container, element, index);
            index++;
        }
        
        return container;
    }
    
    /**
     * Deserialize a JSON object string to an associative container (Map, UnorderedMap).
     * 
     * @tparam MapType The map type to deserialize to (e.g., Map<StdString, ProductX>, UnorderedMap<int, Person>)
     * @param input The JSON object string
     * @return The deserialized map
     */
    template<typename MapType>
    static MapType deserialize_associative_container(const StdString& input) {
        // Parse the JSON string into a JsonDocument
        JsonDocument doc;
        DeserializationError error = deserializeJson(doc, input.c_str());
        
        if (error != DeserializationError::Ok) {
            throw std::invalid_argument("Failed to parse JSON: " + input);
        }
        
        // Check if it's an object
        if (!doc.is<JsonObject>()) {
            throw std::invalid_argument("Expected JSON object, got: " + input);
        }
        
        JsonObject jsonObject = doc.as<JsonObject>();
        MapType map;
        
        // Get the key and value types
        using KeyType = typename MapType::key_type;
        using ValueType = typename MapType::mapped_type;
        
        // Iterate through each key-value pair in the JSON object
        for (JsonPair pair : jsonObject) {
            // Deserialize the key
            KeyType key;
            if constexpr (is_primitive_type_v<KeyType>) {
                if constexpr (std::is_same_v<KeyType, StdString> ||
                             std::is_same_v<KeyType, CStdString> ||
                             std::is_same_v<KeyType, std::string>) {
                    key = KeyType(pair.key().c_str());
                } else if constexpr (std::is_same_v<KeyType, bool> ||
                                     std::is_same_v<KeyType, Bool> ||
                                     std::is_same_v<KeyType, CBool>) {
                    StdString keyStr = StdString(pair.key().c_str());
                    key = convert_string_to_primitive<KeyType>(keyStr);
                } else if constexpr (std::is_integral_v<KeyType>) {
                    StdString keyStr = StdString(pair.key().c_str());
                    key = convert_string_to_primitive<KeyType>(keyStr);
                } else if constexpr (std::is_floating_point_v<KeyType>) {
                    StdString keyStr = StdString(pair.key().c_str());
                    key = convert_string_to_primitive<KeyType>(keyStr);
                } else {
                    StdString keyStr = StdString(pair.key().c_str());
                    key = convert_string_to_primitive<KeyType>(keyStr);
                }
            } else {
                // For complex key types, deserialize from JSON string
                StdString keyJson = StdString(pair.key().c_str());
                key = KeyType::Deserialize(keyJson);
            }
            
            // Deserialize the value
            ValueType value;
            if constexpr (is_primitive_type_v<ValueType>) {
                // For primitive types, extract directly from JSON
                if constexpr (std::is_same_v<ValueType, bool> ||
                             std::is_same_v<ValueType, Bool> ||
                             std::is_same_v<ValueType, CBool>) {
                    value = pair.value().as<bool>();
                } else if constexpr (std::is_same_v<ValueType, StdString> ||
                                     std::is_same_v<ValueType, CStdString> ||
                                     std::is_same_v<ValueType, std::string>) {
                    const char* str = pair.value().as<const char*>();
                    value = ValueType(str ? str : "");
                } else if constexpr (std::is_integral_v<ValueType>) {
                    if constexpr (std::is_signed_v<ValueType>) {
                        value = static_cast<ValueType>(pair.value().as<int64_t>());
                    } else {
                        value = static_cast<ValueType>(pair.value().as<uint64_t>());
                    }
                } else if constexpr (std::is_floating_point_v<ValueType>) {
                    value = static_cast<ValueType>(pair.value().as<double>());
                } else {
                    // Fallback for other primitive types
                    StdString valueStr;
                    serializeJson(pair.value(), valueStr);
                    value = convert_string_to_primitive<ValueType>(valueStr);
                }
            } else {
                // For complex types, serialize the value to JSON string and call Deserialize
                StdString valueJson;
                serializeJson(pair.value(), valueJson);
                value = ValueType::Deserialize(valueJson);
            }
            
            // Insert into map
            map[key] = value;
        }
        
        return map;
    }
    
    /**
     * Serialize an associative container (map, unordered_map) to JSON object.
     */
    template<typename Map>
    static StdString serialize_associative_container(const Map& map) {
        JsonDocument doc;
        JsonObject obj = doc.to<JsonObject>();
        
        for (const auto& pair : map) {
            // Serialize key
            StdString keyJson = Serialize(pair.first);
            StdString keyStr;
            
            if (is_primitive_type_v<typename Map::key_type>) {
                if constexpr (std::is_same_v<typename Map::key_type, StdString> ||
                              std::is_same_v<typename Map::key_type, CStdString> ||
                              std::is_same_v<typename Map::key_type, std::string>) {
                    keyStr = pair.first;
                } else {
                    keyStr = keyJson;
                }
            } else {
                // For complex key types, use the serialized JSON as key (may need adjustment)
                keyStr = keyJson;
            }
            
            // Serialize value
            StdString valueJson = Serialize(pair.second);
            
            // Parse value JSON and add to object
            JsonDocument valueDoc;
            DeserializationError error = deserializeJson(valueDoc, valueJson.c_str());
            if (error == DeserializationError::Ok) {
                obj[keyStr.c_str()] = valueDoc.as<JsonVariant>();
            } else {
                // If value is primitive, add directly
                if (is_primitive_type_v<typename Map::mapped_type>) {
                    if constexpr (std::is_same_v<typename Map::mapped_type, bool> ||
                                  std::is_same_v<typename Map::mapped_type, Bool> ||
                                  std::is_same_v<typename Map::mapped_type, CBool>) {
                        obj[keyStr.c_str()] = pair.second;
                    } else if constexpr (std::is_same_v<typename Map::mapped_type, StdString> ||
                                         std::is_same_v<typename Map::mapped_type, CStdString> ||
                                         std::is_same_v<typename Map::mapped_type, std::string>) {
                        obj[keyStr.c_str()] = pair.second.c_str();
                    } else if constexpr (std::is_integral_v<typename Map::mapped_type>) {
                        obj[keyStr.c_str()] = static_cast<int64_t>(pair.second);
                    } else if constexpr (std::is_floating_point_v<typename Map::mapped_type>) {
                        obj[keyStr.c_str()] = static_cast<double>(pair.second);
                    } else {
                        obj[keyStr.c_str()] = valueJson.c_str();
                    }
                } else {
                    // For complex types, parse and add
                    JsonDocument valDoc;
                    if (deserializeJson(valDoc, valueJson.c_str()) == DeserializationError::Ok) {
                        obj[keyStr.c_str()] = valDoc.as<JsonVariant>();
                    } else {
                        obj[keyStr.c_str()] = valueJson.c_str();
                    }
                }
            }
        }
        
        StdString output;
        serializeJson(doc, output);
        return StdString(output.c_str());
    }
};

/**
 * Helper function to serialize a value.
 * Handles primitives, enums (via template specialization), and serializable objects.
 * 
 * @tparam T The type to serialize
 * @param value The value to serialize
 * @return StdString representation of the value
 */
template<typename T>
StdString SerializeValue(const T& value) {
    // Check if primitive type
    constexpr bool is_primitive = 
        std::is_same_v<T, int> || std::is_same_v<T, unsigned int> ||
        std::is_same_v<T, long> || std::is_same_v<T, unsigned long> ||
        std::is_same_v<T, short> || std::is_same_v<T, unsigned short> ||
        std::is_same_v<T, char> || std::is_same_v<T, unsigned char> ||
        std::is_same_v<T, bool> || std::is_same_v<T, float> ||
        std::is_same_v<T, double> || std::is_same_v<T, size_t> ||
        std::is_same_v<T, Int> || std::is_same_v<T, CInt> ||
        std::is_same_v<T, UInt> || std::is_same_v<T, CUInt> ||
        std::is_same_v<T, Long> || std::is_same_v<T, CLong> ||
        std::is_same_v<T, ULong> || std::is_same_v<T, CULong> ||
        std::is_same_v<T, UInt8> ||
        std::is_same_v<T, Char> || std::is_same_v<T, CChar> ||
        std::is_same_v<T, UChar> || std::is_same_v<T, CUChar> ||
        std::is_same_v<T, Bool> || std::is_same_v<T, CBool> ||
        std::is_same_v<T, Size> || std::is_same_v<T, CSize> ||
        std::is_same_v<T, StdString> || std::is_same_v<T, CStdString>;
    
    if constexpr (is_primitive) {
        // Handle primitive types
        return SerializationUtility::convert_primitive_to_string(value);
    } else if constexpr (std::is_enum_v<T>) {
        // Handle enum types - template specialization should be provided by S8_handle_enum_serialization.py
        // The specialization will be automatically selected by the compiler when calling Serialize<T>
        // We need to explicitly call it to use the specialization
        // Note: This will use the specialization if it exists, otherwise it will fail to compile
        // which is what we want - enums must have specializations
        return SerializationUtility::Serialize<T>(value);
    } else {
        // Handle serializable objects - call .Serialize() method
        return value.Serialize();
    }
}

/**
 * Helper function to deserialize a value.
 * Handles primitives, enums (via template specialization), containers, and serializable objects.
 * 
 * @tparam ReturnType The type to deserialize to
 * @param input The string input to deserialize
 * @return The deserialized value of type ReturnType
 */
template<typename ReturnType>
ReturnType DeserializeValue(const StdString& input) {
    // Check if primitive type
    constexpr bool is_primitive = 
        std::is_same_v<ReturnType, int> || std::is_same_v<ReturnType, unsigned int> ||
        std::is_same_v<ReturnType, long> || std::is_same_v<ReturnType, unsigned long> ||
        std::is_same_v<ReturnType, short> || std::is_same_v<ReturnType, unsigned short> ||
        std::is_same_v<ReturnType, char> || std::is_same_v<ReturnType, unsigned char> ||
        std::is_same_v<ReturnType, bool> || std::is_same_v<ReturnType, float> ||
        std::is_same_v<ReturnType, double> || std::is_same_v<ReturnType, size_t> ||
        std::is_same_v<ReturnType, Int> || std::is_same_v<ReturnType, CInt> ||
        std::is_same_v<ReturnType, UInt> || std::is_same_v<ReturnType, CUInt> ||
        std::is_same_v<ReturnType, Long> || std::is_same_v<ReturnType, CLong> ||
        std::is_same_v<ReturnType, ULong> || std::is_same_v<ReturnType, CULong> ||
        std::is_same_v<ReturnType, UInt8> ||
        std::is_same_v<ReturnType, Char> || std::is_same_v<ReturnType, CChar> ||
        std::is_same_v<ReturnType, UChar> || std::is_same_v<ReturnType, CUChar> ||
        std::is_same_v<ReturnType, Bool> || std::is_same_v<ReturnType, CBool> ||
        std::is_same_v<ReturnType, Size> || std::is_same_v<ReturnType, CSize> ||
        std::is_same_v<ReturnType, StdString> || std::is_same_v<ReturnType, CStdString>;
    
    if constexpr (is_primitive) {
        // Handle primitive types
        return SerializationUtility::convert_string_to_primitive<ReturnType>(input);
    } else if constexpr (std::is_enum_v<ReturnType>) {
        // Handle enum types - use template specialization if available
        return SerializationUtility::Deserialize<ReturnType>(input);
    } else if constexpr (SerializationUtility::is_sequential_container_v<ReturnType> || 
                         SerializationUtility::is_associative_container_v<ReturnType>) {
        // Handle containers - use SerializationUtility::Deserialize
        return SerializationUtility::Deserialize<ReturnType>(input);
    } else {
        // Handle serializable objects - call static Deserialize() method
        return ReturnType::Deserialize(input);
    }
}

} // namespace serializer
} // namespace nayan

#endif // SERIALIZATION_UTILITY_H
