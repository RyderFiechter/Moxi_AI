import "hardhat/types/runtime";

declare module "hardhat/types/runtime" {
  interface HardhatRuntimeEnvironment {
    ethers: typeof import("ethers");
  }
}

declare module "hardhat" {
  export const ethers: typeof import("ethers");
}

