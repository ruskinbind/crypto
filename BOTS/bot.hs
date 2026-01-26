{-# LANGUAGE TemplateHaskell, RankNTypes, ScopedTypeVariables, FlexibleContexts #-}
{-# LANGUAGE DeriveGeneric, DeriveAnyClass, BangPatterns #-}

module InsaneML where

import Control.Concurrent.STM
import Control.Monad.State.Strict
import Control.Monad.Reader
import Control.Lens
import GHC.Generics (Generic)
import System.Random
import Data.Vector (Vector, (!), (//))
import qualified Data.Vector as V
import Linear.V2
import Linear.Matrix
import Linear.Vector

-- Ek bilkul bekaar complicated type synonym sirf dikhane ke liye
type Tensor a = Vector (Vector (V2 a))

data Activation = ReLU | Tanh | Softmax deriving (Show, Eq)

data Layer = Layer
  { _weights :: !(Vector (Vector Double))
  , _biases  :: !(Vector Double)
  , _actFn   :: Activation
  } deriving (Show, Generic)

makeLenses ''Layer

data Network = Network
  { _layers     :: [Layer]
  , _learningRate :: Double
  , _momentum   :: TVar (Vector (Vector Double))  -- STM mein momentum rakha kyuki kyun nahi
  } deriving (Generic)

makeLenses ''Network

-- Lens for Network
makeLenses ''Network

-- Complicated initializer jo sach mein kaam karta hai
xavierInit :: Int -> Int -> IO (Vector (Vector Double))
xavierInit inSz outSz = do
  g <- newStdGen
  let bound = sqrt (1.0 / fromIntegral inSz)
      vs = take (inSz * outSz) $ randomRs (-bound, bound) g
  return . V.fromList . chunksOf inSz $ vs

chunksOf :: Int -> [a] -> [[a]]
chunksOf _ [] = []
chunksOf n xs = take n xs : chunksOf n (drop n xs)

-- Forward pass with lens and State monad (kyunki simple function se mazaa nahi aa raha tha)
forward :: Vector Double -> StateT Network IO (Vector Double)
forward input = do
  net <- get
  let go :: Vector Double -> [Layer] -> StateT Network IO (Vector Double)
      go x [] = return x
      go x (l:ls) = do
        w <- liftIO $ readTVarIO (net ^. momentum)  -- momentum padho
        let z = (V.fromList $ map (V.map V.fromList $ _weights l) !*! V.fromList [x]) V.sum + _biases l
            a = case _actFn l of
                  ReLU -> V.map (max 0) z
                  Tanh -> V.map tanh z
                  Softmax -> let expZ = V.map exp (z - V.maximum z)
                             in expZ V.map (/ V.sum expZ) expZ
        go a ls
  go input (net ^. layers)

-- Backprop with ReaderT + StateT + STM (maximum overkill)
backprop :: Vector Double -> Vector Double -> Vector Double -> ReaderT Double (StateT Network STM) ()
backprop lr target output = do
  eta <- ask
  net <- lift get
  let error = V.zipWith (-) target output
      updateLayer _ [] = return ()
      updateLayer prevErr (l:ls) = do
        let grad = V.map (* prevErr ! i) input  -- simplified
        -- momentum update with TVar
        mom <- lift $ readTVar (net ^. momentum)
        let newMom = V.zipWith (zipWith (+)) mom (V.map (*0.9) mom + (1-0.9)*grad))
        lift $ modifyTVar' (net ^. momentum) (const newMom)
        let deltaW = V.map (* (eta * lr)) newMom
        -- actual weight update
        lift $ layers . traverse . weights %~ \w -> V.zipWith (V.zipWith (+)) w deltaW
        -- bias update
        lift $ layers . traverse . biases %~ V.zipWith (+) (V.map (* (eta * lr)) error)

  updateLayer error (reverse $ net ^. layers)

-- Training loop jo 1000 epochs tak chalega aur har epoch mein STM use karega
trainInsaneNetwork :: Int -> [(Vector Double, Vector Double)] -> IO Network
trainInsaneNetwork epochs dataset = do
  -- 3-layer network: 784 -> 256 -> 128 -> 10 (MNIST style)
  w1 <- xavierInit 784 256
  w2 <- xavierInit 256 128
  w3 <- xavierInit 128 10
  let layers' = 
        [ Layer w1 (V.replicate 256 0.0) ReLU
        , Layer w2 (V.replicate 128 0.0) ReLU
        , Layer w3 (V.replicate 10 0.0) Softmax
        ]
  mom <- newTVarIO $ V.replicate (maximum $ map (length . concat . map V.toList . V.toList . _weights) layers') 0.0
  net <- newTVarIO $ Network layers' 0.001 mom

  let loop 0 = return ()
      loop n = do
        forM_ dataset $ \(inp, tgt) -> do
          out <- evalStateT (forward inp) =<< readTVarIO net
          atomically $ runReaderT (backprop 0.01 tgt out) 1.0 $ modifyTVar net
        print $ "Epoch " ++ show (epochs - n + 1) ++ " completed"
        loop (n-1)

  -- recursive loop kyuki tail recursion is love

  loop epochs
  readTVarIO net

-- Main (comment out if you don't want to run)
-- main :: IO ()
-- main = do
--   let dummyData = replicate 100 (V.replicate 784 0.5, V.replicate 10 0.0 // [(0,1.0)])
--   trained <- trainInsaneNetwork 100 dummyData
--   print "Training completed with over 9000 complications"
