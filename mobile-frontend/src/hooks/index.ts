import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import NetInfo from "@react-native-community/netinfo";
import AsyncStorage from "@react-native-async-storage/async-storage";

export const useApiQuery = (
  key: string | string[],
  queryFn: () => Promise<any>,
  options?: any,
) => {
  return useQuery(key, queryFn, {
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    ...options,
  });
};

export const useApiMutation = (
  mutationFn: (variables: any) => Promise<any>,
  options?: any,
) => {
  const queryClient = useQueryClient();

  return useMutation(mutationFn, {
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
    ...options,
  });
};

export const useNetworkStatus = () => {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [connectionType, setConnectionType] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsConnected(state.isConnected);
      setConnectionType(state.type);
    });

    return () => unsubscribe();
  }, []);

  return { isConnected, connectionType };
};

export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

export const useAsyncStorage = (key: string, initialValue?: any) => {
  const [storedValue, setStoredValue] = useState(initialValue);
  const [loading, setLoading] = useState(true);

  const setValue = useCallback(
    async (value: any) => {
      try {
        const valueToStore =
          value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        await AsyncStorage.setItem(key, JSON.stringify(valueToStore));
      } catch (error) {
        console.error(`Error setting ${key} in AsyncStorage:`, error);
      }
    },
    [key, storedValue],
  );

  const getValue = useCallback(async () => {
    try {
      setLoading(true);
      const item = await AsyncStorage.getItem(key);
      if (item) {
        const parsedItem = JSON.parse(item);
        setStoredValue(parsedItem);
        return parsedItem;
      }
      return initialValue;
    } catch (error) {
      console.error(`Error getting ${key} from AsyncStorage:`, error);
      return initialValue;
    } finally {
      setLoading(false);
    }
  }, [key, initialValue]);

  const removeValue = useCallback(async () => {
    try {
      await AsyncStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.error(`Error removing ${key} from AsyncStorage:`, error);
    }
  }, [key, initialValue]);

  useEffect(() => {
    getValue();
  }, [getValue]);

  return { storedValue, setValue, removeValue, loading };
};

export const useFormValidation = (initialValues: any, validationRules: any) => {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const validateField = useCallback(
    (name: string, value: any) => {
      const rule = validationRules[name];
      if (!rule) return "";

      if (rule.required && (!value || value.toString().trim() === "")) {
        return rule.requiredMessage || `${name} is required`;
      }

      if (rule.minLength && value.length < rule.minLength) {
        return (
          rule.minLengthMessage ||
          `${name} must be at least ${rule.minLength} characters`
        );
      }

      if (rule.maxLength && value.length > rule.maxLength) {
        return (
          rule.maxLengthMessage ||
          `${name} must be no more than ${rule.maxLength} characters`
        );
      }

      if (rule.pattern && !rule.pattern.test(value)) {
        return rule.patternMessage || `${name} format is invalid`;
      }

      if (rule.custom && typeof rule.custom === "function") {
        return rule.custom(value) || "";
      }

      return "";
    },
    [validationRules],
  );

  const validateForm = useCallback(() => {
    const newErrors: Record<string, string> = {};
    let isValid = true;

    Object.keys(validationRules).forEach((field) => {
      const error = validateField(field, values[field]);
      if (error) {
        newErrors[field] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  }, [values, validateField, validationRules]);

  const handleChange = useCallback(
    (name: string, value: any) => {
      setValues((prev: any) => ({ ...prev, [name]: value }));

      if (touched[name]) {
        const error = validateField(name, value);
        setErrors((prev) => ({ ...prev, [name]: error }));
      }
    },
    [touched, validateField],
  );

  const handleBlur = useCallback(
    (name: string) => {
      setTouched((prev) => ({ ...prev, [name]: true }));
      const error = validateField(name, values[name]);
      setErrors((prev) => ({ ...prev, [name]: error }));
    },
    [values, validateField],
  );

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    validateForm,
    reset,
    isValid: Object.keys(errors).length === 0,
  };
};

export const usePagination = (data: any[], itemsPerPage: number = 10) => {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(data.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentData = data.slice(startIndex, endIndex);

  const goToPage = useCallback(
    (page: number) => {
      if (page >= 1 && page <= totalPages) {
        setCurrentPage(page);
      }
    },
    [totalPages],
  );

  const nextPage = useCallback(() => {
    goToPage(currentPage + 1);
  }, [currentPage, goToPage]);

  const prevPage = useCallback(() => {
    goToPage(currentPage - 1);
  }, [currentPage, goToPage]);

  const reset = useCallback(() => {
    setCurrentPage(1);
  }, []);

  return {
    currentPage,
    totalPages,
    currentData,
    goToPage,
    nextPage,
    prevPage,
    reset,
    hasNext: currentPage < totalPages,
    hasPrev: currentPage > 1,
  };
};
