import Constants from 'expo-constants'
import { Platform } from 'react-native'

function defaultApiBase(): string {
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000'
  }
  return 'http://localhost:8000'
}

export const API_BASE =
  process.env.EXPO_PUBLIC_API_URL ||
  (Constants.expoConfig?.extra?.apiUrl as string | undefined) ||
  defaultApiBase()

export const APP_NAME = 'Levera'
