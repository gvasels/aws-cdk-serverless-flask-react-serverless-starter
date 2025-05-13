import { Amplify } from "aws-amplify";

// Define the shape of the Amplify config matching your template structure
export interface AmplifyConfig {
  Auth: {
    Cognito: {
      userPoolClientId: string;
      userPoolId: string;
      loginWith: {
        username: boolean;
        email?: boolean;
      };
      region?: string;
    }
  },
  API: {
    REST: {
      [apiName: string]: {
        endpoint: string;
      };
    };
  };
}

// Declare amplifyConfig variable with the appropriate type
let amplifyConfig: AmplifyConfig;

// Import the template config for fallback
import amplifyConfigTemplate from './amplify-config';

// Use dynamic import() for the local config file
const loadConfig = async (): Promise<AmplifyConfig> => {
  try {
    // Try to import the local configuration file
    const localConfig = await import('./amplify-config.local.ts');
    console.log("Using local Amplify configuration");
    return localConfig.default;
  } catch {
    // If the local file doesn't exist, use the template as a fallback
    console.error("Local Amplify configuration file not found. Using template instead.");
    console.error("Please copy amplify-config.js to amplify-config.local.js and update with your own values.");
    return amplifyConfigTemplate;
  }
};

// Initialize config asynchronously
const configPromise = loadConfig();


// Function to initialize Amplify
export const configureAmplify = async (): Promise<void> => {
  amplifyConfig = await configPromise;
  Amplify.configure(amplifyConfig);
};

// Export the configuration for any component that needs direct access
export const getAmplifyConfig = async (): Promise<AmplifyConfig> => {
  return await configPromise;
};

// For synchronous access after initial load
export const getAmplifyConfigSync = (): AmplifyConfig | undefined => {
  if (amplifyConfig) {
    return amplifyConfig;
  }
  console.warn("Amplify config not yet loaded. Consider using the async getAmplifyConfig() instead.");
  return undefined;
};