"""
有機化合物立体構造シミュレーターのコアモジュール
"""

import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Crippen, Lipinski
from rdkit.Chem.rdMolDescriptors import CalcTPSA, CalcNumRotatableBonds
from typing import Optional, Dict, Any
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MolecularSimulator:
    """有機化合物の立体構造シミュレーションを行うクラス"""
    
    def __init__(self):
        self.molecule = None
        self.mol_block = None
        self.properties = {}
        
    def create_molecule_from_smiles(self, smiles: str) -> bool:
        """
        SMILES記法から分子オブジェクトを作成
        
        Args:
            smiles: SMILES記法の文字列
            
        Returns:
            bool: 成功時True、失敗時False
        """
        try:
            # SMILES記法から分子を生成
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logger.error(f"Invalid SMILES: {smiles}")
                return False
                
            # 水素原子を追加
            mol = Chem.AddHs(mol)
            self.molecule = mol
            logger.info(f"Successfully created molecule from SMILES: {smiles}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating molecule from SMILES: {e}")
            return False
    
    def optimize_3d_structure(self, max_iters: int = 200) -> bool:
        """
        3D構造の生成とエネルギー最適化
        
        Args:
            max_iters: 最適化の最大反復回数
            
        Returns:
            bool: 成功時True、失敗時False
        """
        if self.molecule is None:
            logger.error("No molecule to optimize")
            return False
            
        try:
            # 3D座標を生成
            AllChem.EmbedMolecule(self.molecule, randomSeed=42)
            
            # UFF (Universal Force Field) を使用してエネルギー最適化
            result = AllChem.UFFOptimizeMolecule(self.molecule, maxIters=max_iters)
            
            if result == 0:
                logger.info("Structure optimization converged successfully")
            else:
                logger.warning(f"Structure optimization did not converge (result: {result})")
                
            # MOLブロック形式で構造データを保存
            self.mol_block = Chem.MolToMolBlock(self.molecule)
            return True
            
        except Exception as e:
            logger.error(f"Error during 3D structure optimization: {e}")
            return False
    
    def calculate_properties(self) -> Dict[str, Any]:
        """
        分子の物理化学的性質を計算
        
        Returns:
            Dict: 計算された分子特性
        """
        if self.molecule is None:
            return {}
            
        try:
            properties = {
                # 基本的な分子特性
                'molecular_weight': Descriptors.MolWt(self.molecule),
                'exact_mass': Descriptors.ExactMolWt(self.molecule),
                'formula': Chem.rdMolDescriptors.CalcMolFormula(self.molecule),
                
                # Lipinski's Rule of Five 関連
                'logp': Crippen.MolLogP(self.molecule),
                'hbd': Lipinski.NumHDonors(self.molecule),  # 水素結合供与体数
                'hba': Lipinski.NumHAcceptors(self.molecule),  # 水素結合受容体数
                'tpsa': CalcTPSA(self.molecule),  # 極性表面積
                
                # その他の特性
                'rotatable_bonds': CalcNumRotatableBonds(self.molecule),
                'heavy_atoms': self.molecule.GetNumHeavyAtoms(),
                'rings': Chem.rdMolDescriptors.CalcNumRings(self.molecule),
                'aromatic_rings': Chem.rdMolDescriptors.CalcNumAromaticRings(self.molecule),
                
                # Drug-likeness 評価
                'lipinski_violations': self._count_lipinski_violations(),
            }
            
            self.properties = properties
            logger.info("Molecular properties calculated successfully")
            return properties
            
        except Exception as e:
            logger.error(f"Error calculating molecular properties: {e}")
            return {}
    
    def _count_lipinski_violations(self) -> int:
        """Lipinski's Rule of Five の違反数をカウント"""
        violations = 0
        
        if self.properties.get('molecular_weight', 0) > 500:
            violations += 1
        if self.properties.get('logp', 0) > 5:
            violations += 1
        if self.properties.get('hbd', 0) > 5:
            violations += 1
        if self.properties.get('hba', 0) > 10:
            violations += 1
            
        return violations
    
    def get_mol_block(self) -> Optional[str]:
        """MOLブロック形式の分子データを取得"""
        return self.mol_block
    
    def get_molecule(self) -> Optional[Chem.Mol]:
        """RDKit分子オブジェクトを取得"""
        return self.molecule
    
    def get_properties_dataframe(self) -> pd.DataFrame:
        """分子特性をDataFrame形式で取得"""
        if not self.properties:
            return pd.DataFrame()
            
        # データを整理してDataFrameに変換
        data = []
        for key, value in self.properties.items():
            if isinstance(value, (int, float)):
                data.append({
                    'Property': key.replace('_', ' ').title(),
                    'Value': f"{value:.3f}" if isinstance(value, float) else str(value),
                    'Unit': self._get_unit(key)
                })
            else:
                data.append({
                    'Property': key.replace('_', ' ').title(),
                    'Value': str(value),
                    'Unit': ''
                })
                
        return pd.DataFrame(data)
    
    def _get_unit(self, property_name: str) -> str:
        """各特性の単位を返す"""
        units = {
            'molecular_weight': 'g/mol',
            'exact_mass': 'g/mol',
            'tpsa': 'Ų',
            'logp': '',
            'hbd': 'count',
            'hba': 'count',
            'rotatable_bonds': 'count',
            'heavy_atoms': 'count',
            'rings': 'count',
            'aromatic_rings': 'count',
            'lipinski_violations': 'count'
        }
        return units.get(property_name, '')


# よく使われる有機化合物のプリセット
PRESET_MOLECULES = {
    'エタノール (Ethanol)': 'CCO',
    'メタン (Methane)': 'C',
    'ベンゼン (Benzene)': 'c1ccccc1',
    'アスピリン (Aspirin)': 'CC(=O)OC1=CC=CC=C1C(=O)O',
    'カフェイン (Caffeine)': 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
    'グルコース (Glucose)': 'C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O',
    'アセトン (Acetone)': 'CC(=O)C',
    'トルエン (Toluene)': 'Cc1ccccc1',
    'フェノール (Phenol)': 'c1ccc(cc1)O',
    '酢酸 (Acetic Acid)': 'CC(=O)O',
    'アンモニア (Ammonia)': 'N',
    '水 (Water)': 'O',
    'エチレン (Ethylene)': 'C=C',
    'プロパン (Propane)': 'CCC',
    'シクロヘキサン (Cyclohexane)': 'C1CCCCC1',
    'ペニシリン (Penicillin G)': 'CC1(C(N2C(S1)C(C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C',
    'ビタミンC (Vitamin C)': 'C(C(C1C(=O)C(=C(O1)O)O)O)O',
    'ドーパミン (Dopamine)': 'C1=CC(=C(C=C1CCN)O)O',
    'カプサイシン (Capsaicin)': 'CC(C)C=CCCCCC(=O)NCC1=CC(=C(C=C1)O)OC',
    'TNT (Trinitrotoluene)': 'CC1=C(C=C(C=C1[N+](=O)[O-])[N+](=O)[O-])[N+](=O)[O-]'
}


def get_preset_molecules() -> Dict[str, str]:
    """プリセット分子のリストを取得"""
    return PRESET_MOLECULES


if __name__ == "__main__":
    # テスト用のコード
    simulator = MolecularSimulator()
    
    # エタノールでテスト
    if simulator.create_molecule_from_smiles('CCO'):
        if simulator.optimize_3d_structure():
            properties = simulator.calculate_properties()
            print("Molecular Properties:")
            for key, value in properties.items():
                print(f"{key}: {value}")