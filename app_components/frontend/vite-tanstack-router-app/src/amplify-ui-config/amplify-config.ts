import { AmplifyConfig } from './index';

const amplifyConfigTemplate: AmplifyConfig = {
  // Auth Configuration
  Auth: {
    Cognito: {
      userPoolClientId: 'USER_POOL_CLIENT_ID',
      userPoolId: 'USER_POOL_ID',
      loginWith: { // Optional
        username: true,
        email: true // Optional
      }
    }
  },

  // API Configuration
  API: {
    REST: {
      // First API - YourFirstAPIName
      AppSvcAPI: {
        endpoint: 'APPSVC_API_ENDPOINT', //'https://api.execute-api.region.amazonaws.com/stage'
      }
      
      // Add additional API endpoints here as needed
      //FutureSvcAPI: {...}
    }
  }
};

export default amplifyConfigTemplate;